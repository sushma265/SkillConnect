"""
SkillConnect – Analytics Utilities
=====================================
Functions that aggregate data across collections for the analytics
dashboard. Used by both admin and organiser analytics routes.
"""

from typing import Dict, Any, List


def get_platform_analytics() -> Dict[str, Any]:
    """
    Compute platform-wide analytics.

    Returns a dict containing totals for users, events, registrations,
    check-ins, Q&A, polls, networking, and feedback.
    """
    from app.models.user_model import User
    from app.models.event_model import Event
    from app.models.registration_model import Registration
    from app.models.question_model import Question
    from app.models.poll_model import PollVote
    from app.models.networking_model import NetworkingRequest
    from app.models.feedback_model import Feedback

    total_users = User.objects.count()
    total_events = Event.objects.count()
    total_registrations = Registration.objects.count()
    checked_in = Registration.objects(checked_in=True).count()
    total_questions = Question.objects.count()
    answered_questions = Question.objects(is_answered=True).count()
    total_poll_votes = PollVote.objects.count()
    total_connections = NetworkingRequest.objects(
        status="accepted"
    ).count()

    feedbacks = list(Feedback.objects())
    avg_rating = (
        round(sum(f.rating for f in feedbacks) / len(feedbacks), 2)
        if feedbacks
        else 0
    )

    return {
        "users": {
            "total": total_users,
            "by_role": {
                "attendee": User.objects(role="attendee").count(),
                "organizer": User.objects(role="organizer").count(),
                "admin": User.objects(role="admin").count(),
            },
        },
        "events": {"total": total_events},
        "registrations": {
            "total": total_registrations,
            "checked_in": checked_in,
            "attendance_rate": (
                round(checked_in / total_registrations * 100, 1)
                if total_registrations
                else 0
            ),
        },
        "qa": {
            "total_questions": total_questions,
            "answered": answered_questions,
            "answer_rate": (
                round(
                    answered_questions / total_questions * 100, 1
                )
                if total_questions
                else 0
            ),
        },
        "polls": {"total_votes": total_poll_votes},
        "networking": {
            "total_connections": total_connections,
            "pending": NetworkingRequest.objects(
                status="pending"
            ).count(),
        },
        "feedback": {
            "total": len(feedbacks),
            "average_rating": avg_rating,
        },
    }


def get_event_analytics(event) -> Dict[str, Any]:
    """
    Compute analytics for a single event.

    Args:
        event: An Event document instance.

    Returns:
        dict with registration, session, feedback, and networking stats.
    """
    from app.models.registration_model import Registration
    from app.models.session_model import Session
    from app.models.question_model import Question
    from app.models.poll_model import Poll, PollVote
    from app.models.feedback_model import Feedback
    from app.models.networking_model import NetworkingRequest

    regs = Registration.objects(event=event)
    total_regs = regs.count()
    checked_in = regs.filter(checked_in=True).count()

    sessions = list(Session.objects(event=event))
    session_stats = []
    for s in sessions:
        qs = Question.objects(session=s)
        poll_count = Poll.objects(session=s).count()
        votes = sum(
            PollVote.objects(poll=p).count()
            for p in Poll.objects(session=s)
        )
        session_stats.append({
            "session_id": str(s.id),
            "session_title": s.title,
            "questions": qs.count(),
            "answered": qs.filter(is_answered=True).count(),
            "polls": poll_count,
            "poll_votes": votes,
        })

    feedbacks = list(Feedback.objects(event=event))
    avg_rating = (
        round(sum(f.rating for f in feedbacks) / len(feedbacks), 2)
        if feedbacks
        else 0
    )

    net_reqs = NetworkingRequest.objects(event=event)

    return {
        "event": event.to_dict(),
        "registrations": {
            "total": total_regs,
            "checked_in": checked_in,
            "capacity": event.capacity,
            "fill_rate": (
                round(total_regs / event.capacity * 100, 1)
                if event.capacity
                else 0
            ),
            "attendance_rate": (
                round(checked_in / total_regs * 100, 1)
                if total_regs
                else 0
            ),
        },
        "sessions": session_stats,
        "feedback": {
            "total": len(feedbacks),
            "average_rating": avg_rating,
        },
        "networking": {
            "requests": net_reqs.count(),
            "accepted": net_reqs.filter(status="accepted").count(),
        },
    }


def get_participation_data() -> List[Dict[str, Any]]:
    """
    Build participation / fill-rate data for every event.

    Returns:
        List of dicts, one per event, with registration and attendance
        metrics.
    """
    from app.models.event_model import Event
    from app.models.registration_model import Registration

    events = list(Event.objects().order_by("event_date"))
    data = []

    for ev in events:
        regs = Registration.objects(event=ev).count()
        checked = Registration.objects(
            event=ev, checked_in=True
        ).count()

        data.append({
            "event_id": str(ev.id),
            "event_title": ev.title,
            "event_date": (
                ev.event_date.isoformat()
                if ev.event_date
                else None
            ),
            "capacity": ev.capacity,
            "registered": regs,
            "fill_rate": (
                round(regs / ev.capacity * 100, 1)
                if ev.capacity
                else 0
            ),
            "checked_in": checked,
            "attendance_rate": (
                round(checked / regs * 100, 1) if regs else 0
            ),
        })

    return data
