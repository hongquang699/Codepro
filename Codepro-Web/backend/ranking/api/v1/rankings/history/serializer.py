from rest_framework import serializers

class RatingHistoryItemSerializer(serializers.Serializer):
    contest_id = serializers.IntegerField(allow_null=True)
    contest_name = serializers.CharField()
    old_rating = serializers.IntegerField()
    new_rating = serializers.IntegerField()
    rating_change = serializers.IntegerField()
    rank = serializers.IntegerField()
    performance = serializers.IntegerField(allow_null=True)
    date = serializers.CharField()

class UserRatingProfileSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    rating = serializers.IntegerField()
    max_rating = serializers.IntegerField()
    tier = serializers.CharField()
    tier_color = serializers.CharField()
    badge = serializers.CharField()
    contests_participated = serializers.IntegerField()
    history = RatingHistoryItemSerializer(many=True)