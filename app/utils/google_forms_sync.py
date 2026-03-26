"""Shared Google Forms import/sync logic for weekly tests and model sets."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app import db
from app.models import (
    GoogleFormQuestionMap,
    GoogleFormResponseSyncLog,
    ModelSet,
    ModelSetAttempt,
    ModelSetQuestion,
    Question,
    User,
    WeeklyTest,
    WeeklyTestAttempt,
    WeeklyTestQuestion,
)
from app.utils.google_forms import (
    GoogleFormsError,
    extract_answer_text,
    fetch_form,
    list_form_responses,
    normalize_student_id_value,
    parse_google_form_id,
)


@dataclass(frozen=True)
class EntityConfig:
    entity_type: str
    entity_fk: str
    link_model: type[ModelSetQuestion] | type[WeeklyTestQuestion]
    attempt_model: type[ModelSetAttempt] | type[WeeklyTestAttempt]
    question_subject: str
    attempt_time_field: str


ENTITY_CONFIG: dict[str, EntityConfig] = {
    'model_set': EntityConfig(
        entity_type='model_set',
        entity_fk='model_set_id',
        link_model=ModelSetQuestion,
        attempt_model=ModelSetAttempt,
        question_subject='General',
        attempt_time_field='completed_at',
    ),
    'weekly_test': EntityConfig(
        entity_type='weekly_test',
        entity_fk='test_id',
        link_model=WeeklyTestQuestion,
        attempt_model=WeeklyTestAttempt,
        question_subject='General',
        attempt_time_field='submitted_at',
    ),
}


def _config(entity_type: str) -> EntityConfig:
    try:
        return ENTITY_CONFIG[entity_type]
    except KeyError as err:
        raise GoogleFormsError(f'Unsupported Google sync entity: {entity_type}') from err


def _json_loads(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


def _to_naive_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def _parse_google_datetime(value: str | None) -> datetime | None:
    raw = (value or '').strip()
    if not raw:
        return None
    parsed = datetime.fromisoformat(raw.replace('Z', '+00:00'))
    return _to_naive_utc(parsed)


def _default_subject(entity: ModelSet | WeeklyTest) -> str:
    if isinstance(entity, WeeklyTest):
        return entity.subject or 'General'
    return 'General'


def _cleanup_orphan_questions(question_ids: set[int]) -> None:
    if not question_ids:
        return
    linked_model_set_ids = {
        row.question_id
        for row in ModelSetQuestion.query.filter(ModelSetQuestion.question_id.in_(question_ids)).all()
    }
    linked_weekly_test_ids = {
        row.question_id
        for row in WeeklyTestQuestion.query.filter(WeeklyTestQuestion.question_id.in_(question_ids)).all()
    }
    still_linked = linked_model_set_ids | linked_weekly_test_ids
    orphan_ids = [qid for qid in question_ids if qid not in still_linked]
    if not orphan_ids:
        return
    Question.query.filter(Question.id.in_(orphan_ids)).delete(synchronize_session=False)


def _clear_google_question_inventory(entity_type: str, entity_id: int) -> None:
    cfg = _config(entity_type)
    maps = GoogleFormQuestionMap.query.filter_by(entity_type=entity_type, entity_id=entity_id).all()
    local_question_ids = {m.local_question_id for m in maps if m.local_question_id}
    if local_question_ids:
        db.session.query(cfg.link_model).filter(
            getattr(cfg.link_model, cfg.entity_fk) == entity_id,
            cfg.link_model.question_id.in_(local_question_ids),
        ).delete(synchronize_session=False)
        _cleanup_orphan_questions({int(qid) for qid in local_question_ids})
    GoogleFormQuestionMap.query.filter_by(entity_type=entity_type, entity_id=entity_id).delete(synchronize_session=False)


def _clear_google_runtime_state(entity_type: str, entity_id: int) -> None:
    cfg = _config(entity_type)
    GoogleFormResponseSyncLog.query.filter_by(entity_type=entity_type, entity_id=entity_id).delete(synchronize_session=False)
    db.session.query(cfg.attempt_model).filter(
        getattr(cfg.attempt_model, cfg.entity_fk) == entity_id,
        cfg.attempt_model.source == 'google_forms',
    ).delete(synchronize_session=False)


def reset_google_entity_state(entity_type: str, entity: ModelSet | WeeklyTest) -> None:
    _clear_google_question_inventory(entity_type, entity.id)
    _clear_google_runtime_state(entity_type, entity.id)
    entity.google_student_id_question_id = None
    entity.google_questions_last_imported_at = None
    entity.google_results_last_synced_at = None
    entity.google_last_sync_summary = '{}'
    if isinstance(entity, ModelSet):
        entity.total_questions = ModelSetQuestion.query.filter_by(model_set_id=entity.id).count()


def _extract_form_inventory(form: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    settings = form.get('settings') or {}
    quiz_settings = settings.get('quizSettings') or {}
    email_collection_type = settings.get('emailCollectionType') or 'DO_NOT_COLLECT'
    items = form.get('items') or []
    inventory: list[dict[str, Any]] = []

    for order_index, item in enumerate(items):
        title = (item.get('title') or '').strip()
        description = (item.get('description') or '').strip()
        question = ((item.get('questionItem') or {}).get('question') or {})
        question_id = (question.get('questionId') or '').strip()
        if not question_id:
            continue

        grading = question.get('grading') or {}
        point_value = int(grading.get('pointValue') or 1)
        correct_answers = (grading.get('correctAnswers') or {}).get('answers') or []
        correct_values = [str(answer.get('value') or '').strip() for answer in correct_answers if (answer.get('value') or '').strip()]

        entry = {
            'google_question_id': question_id,
            'title': title or f'Question {order_index + 1}',
            'description': description,
            'question_type': 'unsupported',
            'choice_type': '',
            'options': [],
            'correct_answer': correct_values[0] if correct_values else '',
            'point_value': point_value,
            'order_index': order_index,
            'is_supported': False,
            'is_imported': False,
            'answer_index': None,
        }

        choice_question = question.get('choiceQuestion') or {}
        choice_type = (choice_question.get('type') or '').strip()
        options = [str((opt or {}).get('value') or '').strip() for opt in (choice_question.get('options') or [])]
        options = [value for value in options if value]

        if choice_question:
            entry['question_type'] = 'choice'
            entry['choice_type'] = choice_type
            entry['options'] = options
            if (
                choice_type in {'RADIO', 'DROP_DOWN'}
                and 2 <= len(options) <= 4
                and len(correct_values) == 1
                and correct_values[0] in options
            ):
                entry['is_supported'] = True
                entry['is_imported'] = True
                entry['answer_index'] = options.index(correct_values[0])
        elif question.get('textQuestion') is not None:
            entry['question_type'] = 'text'
        elif question.get('scaleQuestion') is not None:
            entry['question_type'] = 'scale'
        elif question.get('dateQuestion') is not None:
            entry['question_type'] = 'date'
        elif question.get('timeQuestion') is not None:
            entry['question_type'] = 'time'
        else:
            entry['question_type'] = 'unsupported'

        inventory.append(entry)

    meta = {
        'is_quiz': bool(quiz_settings.get('isQuiz')),
        'email_collection_type': email_collection_type,
    }
    return inventory, meta


def _compose_question_text(title: str, description: str) -> str:
    title = (title or '').strip()
    description = (description or '').strip()
    if title and description:
        return f'{title}\n\n{description}'
    return title or description or 'Untitled Question'


def import_google_form_questions(entity_type: str, entity: ModelSet | WeeklyTest) -> dict[str, Any]:
    forms_url = (entity.forms_url or '').strip()
    if not forms_url:
        raise GoogleFormsError('Set a Google Forms URL before importing questions.')

    form_id = parse_google_form_id(forms_url)
    form = fetch_form(form_id)
    inventory, meta = _extract_form_inventory(form)
    if not meta['is_quiz']:
        raise GoogleFormsError('This Google Form is not configured as a quiz. Enable quiz mode before importing.')

    supported = [entry for entry in inventory if entry['is_supported']]
    if not supported:
        raise GoogleFormsError('No supported quiz questions were found. Supported types: single-answer radio/dropdown with 2 to 4 options.')

    _clear_google_question_inventory(entity_type, entity.id)
    _clear_google_runtime_state(entity_type, entity.id)

    subject = _default_subject(entity)
    cfg = _config(entity_type)

    for entry in inventory:
        local_question_id: int | None = None
        if entry['is_imported']:
            question = Question(
                subject=subject,
                text=_compose_question_text(entry['title'], entry['description']),
                options=json.dumps(entry['options']),
                answer_index=int(entry['answer_index'] or 0),
            )
            db.session.add(question)
            db.session.flush()
            local_question_id = question.id

            link = cfg.link_model(
                **{cfg.entity_fk: entity.id, 'question_id': question.id, 'order_index': entry['order_index']}
            )
            db.session.add(link)

        db.session.add(GoogleFormQuestionMap(
            entity_type=entity_type,
            entity_id=entity.id,
            google_question_id=entry['google_question_id'],
            title=entry['title'],
            description=entry['description'],
            question_type=entry['question_type'],
            choice_type=entry['choice_type'],
            options_json=json.dumps(entry['options']),
            correct_answer=entry['correct_answer'],
            point_value=entry['point_value'],
            order_index=entry['order_index'],
            local_question_id=local_question_id,
            is_supported=entry['is_supported'],
            is_imported=entry['is_imported'],
        ))

    entity.google_match_mode = entity.google_match_mode or 'email_then_student_id'
    entity.google_questions_last_imported_at = datetime.utcnow()
    entity.google_results_last_synced_at = None
    entity.google_last_sync_summary = '{}'
    valid_question_ids = {entry['google_question_id'] for entry in inventory}
    if entity.google_student_id_question_id not in valid_question_ids:
        entity.google_student_id_question_id = None
    if isinstance(entity, ModelSet):
        entity.total_questions = len(supported)

    db.session.commit()

    return {
        'form_id': form_id,
        'imported': len(supported),
        'skipped_unsupported': len(inventory) - len(supported),
        'total_detected': len(inventory),
        'email_collection_type': meta['email_collection_type'],
        'is_quiz': meta['is_quiz'],
    }


def _match_user(entity: ModelSet | WeeklyTest, answers: dict[str, Any], respondent_email: str) -> tuple[User | None, str | None, str]:
    email = (respondent_email or '').strip().lower()
    if email:
        user = User.query.filter(db.func.lower(User.email) == email).first()
        if user:
            return user, 'email', ''

    student_id_value = ''
    google_student_id_question_id = (entity.google_student_id_question_id or '').strip()
    if google_student_id_question_id:
        student_id_value = normalize_student_id_value(extract_answer_text(answers.get(google_student_id_question_id)))
        if student_id_value:
            user = User.query.filter_by(student_id=student_id_value).first()
            if user:
                return user, 'student_id', student_id_value

    return None, None, student_id_value


def _review_payload_from_google(entity_type: str, entity_id: int, answers: dict[str, Any]) -> list[dict[str, Any]]:
    review: list[dict[str, Any]] = []
    rows = GoogleFormQuestionMap.query.filter_by(
        entity_type=entity_type,
        entity_id=entity_id,
        is_imported=True,
    ).order_by(GoogleFormQuestionMap.order_index.asc()).all()

    for index, row in enumerate(rows, start=1):
        chosen = extract_answer_text(answers.get(row.google_question_id))
        local_question = row.local_question
        review.append({
            'number': index,
            'subject': local_question.subject if local_question else 'General',
            'text': local_question.text if local_question else row.title,
            'chosen': chosen or 'Not answered',
            'correct': row.correct_answer or '—',
            'isCorrect': bool(chosen and chosen == (row.correct_answer or '')),
        })
    return review


def _score_from_google_inventory(entity_type: str, entity_id: int, answers: dict[str, Any]) -> tuple[int, int]:
    rows = GoogleFormQuestionMap.query.filter_by(entity_type=entity_type, entity_id=entity_id).all()
    if not rows:
        return 0, 0
    total = sum(max(int(row.point_value or 0), 0) for row in rows)
    if total <= 0:
        total = len([row for row in rows if row.is_imported])
    score = 0
    for row in rows:
        chosen = extract_answer_text(answers.get(row.google_question_id))
        if chosen and chosen == (row.correct_answer or ''):
            score += max(int(row.point_value or 0), 1)
    return score, total


def sync_google_form_results(entity_type: str, entity: ModelSet | WeeklyTest) -> dict[str, Any]:
    if not (entity.google_questions_last_imported_at and (entity.forms_url or '').strip()):
        raise GoogleFormsError('Import Google questions first before syncing results.')

    form_id = parse_google_form_id(entity.forms_url)
    responses = list_form_responses(form_id, submitted_after=entity.google_results_last_synced_at)
    cfg = _config(entity_type)

    summary = {
        'processed': 0,
        'matched': 0,
        'unmatched': 0,
        'created': 0,
        'updated': 0,
    }
    latest_sync_at = entity.google_results_last_synced_at

    for response in responses:
        summary['processed'] += 1
        response_id = (response.get('responseId') or '').strip()
        if not response_id:
            continue
        answers = response.get('answers') or {}
        respondent_email = (response.get('respondentEmail') or '').strip().lower()
        submitted_at = _parse_google_datetime(response.get('lastSubmittedTime') or response.get('createTime'))
        if submitted_at and (latest_sync_at is None or submitted_at > latest_sync_at):
            latest_sync_at = submitted_at

        user, matched_by, student_id_value = _match_user(entity, answers, respondent_email)
        review_payload = _review_payload_from_google(entity_type, entity.id, answers)
        computed_score, computed_total = _score_from_google_inventory(entity_type, entity.id, answers)
        score = int(response.get('totalScore')) if response.get('totalScore') is not None else computed_score
        total = computed_total

        log = GoogleFormResponseSyncLog.query.filter_by(
            entity_type=entity_type,
            entity_id=entity.id,
            external_response_id=response_id,
        ).first()
        if not log:
            log = GoogleFormResponseSyncLog(
                entity_type=entity_type,
                entity_id=entity.id,
                external_response_id=response_id,
            )
            db.session.add(log)

        log.respondent_email = respondent_email
        log.student_id_value = student_id_value
        log.matched_user_id = user.id if user else None
        log.matched_by = matched_by
        log.status = 'matched' if user else 'unmatched'
        log.score = score
        log.total = total
        log.submitted_at = submitted_at
        log.payload_json = json.dumps({
            'responseId': response_id,
            'respondentEmail': respondent_email,
            'studentIdValue': student_id_value,
            'answers': {qid: extract_answer_text(answer) for qid, answer in answers.items()},
            'review_questions': review_payload,
            'raw_total_score': response.get('totalScore'),
        })

        if user:
            summary['matched'] += 1
            attempt = cfg.attempt_model.query.filter_by(
                **{cfg.entity_fk: entity.id, 'external_response_id': response_id}
            ).first()
            if attempt is None:
                attempt = cfg.attempt_model(
                    **{cfg.entity_fk: entity.id, 'user_id': user.id}
                )
                attempt.external_response_id = response_id
                attempt.source = 'google_forms'
                db.session.add(attempt)
                summary['created'] += 1
            else:
                summary['updated'] += 1
            attempt.user_id = user.id
            attempt.score = score
            attempt.total = total
            attempt.answers = json.dumps({qid: extract_answer_text(answer) for qid, answer in answers.items()})
            attempt.source = 'google_forms'
            attempt.matched_by = matched_by
            attempt.review_payload = json.dumps(review_payload)
            setattr(attempt, cfg.attempt_time_field, submitted_at or datetime.utcnow())
        else:
            summary['unmatched'] += 1

    entity.google_results_last_synced_at = latest_sync_at or entity.google_results_last_synced_at or datetime.utcnow()
    entity.google_last_sync_summary = json.dumps(summary)
    db.session.commit()
    return summary


def build_internal_review_payload(entity: ModelSet | WeeklyTest, answers: list[Any]) -> list[dict[str, Any]]:
    review: list[dict[str, Any]] = []
    questions = list(entity.questions)
    for index, link in enumerate(questions, start=1):
        question = link.question
        if question is None:
            continue
        selected_idx = answers[index - 1] if index - 1 < len(answers) else -1
        try:
            selected_idx = int(selected_idx)
        except Exception:
            selected_idx = -1
        chosen = question.options and _json_loads(question.options, [])[selected_idx] if 0 <= selected_idx < len(_json_loads(question.options, [])) else 'Not answered'
        options = _json_loads(question.options, [])
        correct = options[question.answer_index] if 0 <= question.answer_index < len(options) else '—'
        review.append({
            'number': index,
            'subject': question.subject or 'General',
            'text': question.text,
            'chosen': chosen,
            'correct': correct,
            'isCorrect': selected_idx == question.answer_index,
        })
    return review


def get_result_for_user(entity_type: str, entity: ModelSet | WeeklyTest, user_id: int) -> dict[str, Any]:
    cfg = _config(entity_type)
    attempt_query = cfg.attempt_model.query.filter_by(**{cfg.entity_fk: entity.id, 'user_id': user_id})
    google_attempt = attempt_query.filter_by(source='google_forms').order_by(getattr(cfg.attempt_model, cfg.attempt_time_field).desc()).first()
    if google_attempt is not None:
        attempt = google_attempt
    else:
        attempt = attempt_query.order_by(getattr(cfg.attempt_model, cfg.attempt_time_field).desc()).first()

    if attempt is None:
        return {'has_result': False}

    review_questions = _json_loads(attempt.review_payload, [])
    if not review_questions and attempt.source != 'google_forms':
        review_questions = build_internal_review_payload(entity, _json_loads(attempt.answers, []))

    total = int(attempt.total or 0)
    score = int(attempt.score or 0)
    submitted_at = getattr(attempt, cfg.attempt_time_field)
    return {
        'has_result': True,
        'score': score,
        'total': total,
        'percentage': round((score / total) * 100) if total > 0 else 0,
        'source': attempt.source or 'internal',
        'matched_by': attempt.matched_by,
        'submitted_at': submitted_at.isoformat() if submitted_at else None,
        'review_questions': review_questions,
    }
