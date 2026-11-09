from rest_framework import serializers

class SearchRankingItemSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    rank = serializers.IntegerField()
    rating = serializers.IntegerField()
    tier = serializers.CharField()
    tier_color = serializers.CharField()
    school = serializers.CharField(allow_blank=True)