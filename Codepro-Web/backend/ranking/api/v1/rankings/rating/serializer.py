from rest_framework import serializers

class RatingLeaderboardItemSerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    rating = serializers.IntegerField()
    max_rating = serializers.IntegerField()
    tier = serializers.CharField()
    tier_color = serializers.CharField()
    badge = serializers.CharField()
    contests_count = serializers.IntegerField()

class RatingLeaderboardResponseSerializer(serializers.Serializer):
    page = serializers.IntegerField()
    page_size = serializers.IntegerField()
    total = serializers.IntegerField()
    items = RatingLeaderboardItemSerializer(many=True)