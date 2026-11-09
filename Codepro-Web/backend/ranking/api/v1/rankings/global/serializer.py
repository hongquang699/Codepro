from rest_framework import serializers

class GlobalRankingItemSerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    rating = serializers.IntegerField()
    score = serializers.FloatField()
    solved = serializers.IntegerField()
    submissions = serializers.IntegerField()
    country = serializers.CharField()
    school = serializers.CharField(allow_blank=True)
    organization = serializers.CharField(allow_null=True)
    tier = serializers.CharField()
    tier_color = serializers.CharField()
    badge = serializers.CharField()
    is_verified = serializers.BooleanField(default=False)

class GlobalRankingResponseSerializer(serializers.Serializer):
    page = serializers.IntegerField()
    page_size = serializers.IntegerField()
    total = serializers.IntegerField()
    items = GlobalRankingItemSerializer(many=True)