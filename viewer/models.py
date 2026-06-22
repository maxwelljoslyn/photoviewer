from django.db import models


class WorkFolder(models.Model):
    """A directory the user has queued up to review photos in."""

    path = models.CharField(max_length=1024, unique=True)
    label = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.label or self.path


class MoveLog(models.Model):
    """Record of a single rating action, used to power undo."""

    GOOD = "good"
    NOT_GOOD = "not_good"
    MAYBE = "maybe"
    RATING_CHOICES = [(GOOD, "Good"), (NOT_GOOD, "Not good"), (MAYBE, "Maybe")]

    folder = models.ForeignKey(
        WorkFolder, on_delete=models.CASCADE, related_name="moves"
    )
    src_path = models.CharField(max_length=1024)
    dest_path = models.CharField(max_length=1024)
    rating = models.CharField(max_length=16, choices=RATING_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    undone = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.rating}: {self.src_path} -> {self.dest_path}"
