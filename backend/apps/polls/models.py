"""业主投票（MOD-013）。"""
from django.db import models


class Poll(models.Model):
    STATUSES = [("OPEN", "进行中"), ("CLOSED", "已截止")]
    KINDS = [("REP_VOTE", "业主代表投票"), ("SURVEY", "调查")]
    SCOPES = [("OWNERS_ONLY", "仅产权业主"), ("OWNERS_AND_RESIDENTS", "产权业主和同住人")]

    creator = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="polls")
    kind = models.CharField(max_length=16, choices=KINDS, default="SURVEY")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    survey_scope = models.CharField(max_length=32, choices=SCOPES, null=True, blank=True)
    deadline = models.DateTimeField()
    status = models.CharField(max_length=8, choices=STATUSES, default="OPEN")
    participant_count = models.IntegerField(null=True, blank=True)
    result_snapshot = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]


class Question(models.Model):
    QTYPES = [("AGREE_OPPOSE_ABSTAIN", "同意/反对/弃权"), ("SCORE", "打分"), ("SINGLE", "单选"),
              ("MULTI", "多选"), ("TEXT", "文本")]

    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="questions")
    title = models.CharField(max_length=500)
    qtype = models.CharField(max_length=32, choices=QTYPES, default="SINGLE")
    required = models.BooleanField(default=True)
    options = models.JSONField(default=list)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]


class Participant(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="participants")
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="poll_participations")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["poll", "user"], name="uniq_poll_participant")]


class PollResponse(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="responses")
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="poll_responses")
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["poll", "user"], name="uniq_poll_response")]


class PollAnswer(models.Model):
    response = models.ForeignKey(PollResponse, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers")
    value = models.CharField(max_length=200)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["response", "question"], name="uniq_poll_answer_question")
        ]
