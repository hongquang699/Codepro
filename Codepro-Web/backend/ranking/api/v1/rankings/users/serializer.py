from rest_framework import serializers

class UserRankingDetailSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    global_rank = serializers.IntegerField()
    rating = serializers.IntegerField()
    max_rating = serializers.IntegerField()
    tier = serializers.CharField()
    tier_color = serializers.CharField()
    badge = serializers.CharField()
    score = serializers.FloatField()
    solved = serializers.IntegerField()
    submissions = serializers.IntegerField()
    contests_count = serializers.IntegerField()
    country = serializers.CharField()
    school = serializers.CharField(allow_blank=True)