from django.db import models

# Create your models here.
class subscription(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="created_subscription_plans"
    )

    plan_name = models.CharField(
        max_length=100,
        unique=True
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    messages_limit = models.PositiveIntegerField(null=True, blank=True)
    duration_days = models.PositiveIntegerField()

    trial_package = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.plan_name

class UserSubscription(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="user_subscription"
    )

    plan = models.ForeignKey(
        subscription,
        on_delete=models.PROTECT,
        related_name="user_subscriptions"
    )

    start_date = models.DateTimeField(auto_now_add=True)

    end_date = models.DateTimeField()

    messages_used = models.PositiveIntegerField(default=0)

    active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} - {self.plan.plan_name}"