from rest_framework import serializers

from habit.models import Habit


class HabitNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Habit
        fields = ["id", "action", "is_pleasant", "place", "time"]


class HabitSerializer(serializers.ModelSerializer):
    related_habit = HabitNestedSerializer(read_only=True)
    related_habit_id = serializers.PrimaryKeyRelatedField(
        queryset=Habit.objects.filter(is_pleasant=True),
        source="related_habit",
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Habit
        fields = [
            "id",
            "user",
            "action",
            "place",
            "time",
            "is_pleasant",
            "related_habit",
            "related_habit_id",
            "periodicity",
            "reward",
            "duration_minutes",
            "is_public",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["user", "created_at", "updated_at"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)

    @staticmethod
    def _strip_reward(value):
        return value.strip() if isinstance(value, str) else ""

    def validate(self, attrs):
        reward = attrs.get(
            "reward", getattr(self.instance, "reward", None) if self.instance else None
        )
        related = attrs.get(
            "related_habit",
            getattr(self.instance, "related_habit", None) if self.instance else None,
        )
        is_pleasant = attrs.get(
            "is_pleasant",
            getattr(self.instance, "is_pleasant", False) if self.instance else False,
        )

        if reward and related:
            raise serializers.ValidationError(
                "Нельзя одновременно указывать и награду, и связанную привычку."
            )

        if related and not related.is_pleasant:
            raise serializers.ValidationError(
                "В связанную привычку можно поставить только приятную."
            )

        if is_pleasant and (reward or related):
            raise serializers.ValidationError(
                "У приятной привычки не может быть награды или связанной привычки."
            )

        return attrs

    def validate_periodicity(self, value):
        if value < 1 or value > 7:
            raise serializers.ValidationError(
                "Периодичность должна быть от 1 до 7 дней."
            )
        return value

    def validate_duration_minutes(self, value):
        if value < 1 or value > 2:
            raise serializers.ValidationError(
                "Время выполнения не может быть больше 2 минут."
            )
        return value
