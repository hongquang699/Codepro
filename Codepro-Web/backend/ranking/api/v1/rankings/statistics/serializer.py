from rest_framework import serializers

class RankingStatisticsSerializer(serializers.Serializer):
    total_ranked_users = serializers.IntegerField()
    total_submissions = serializers.IntegerField()
    total_solved = serializers.IntegerField()
    tier_distribution = serializers.DictField()
    top_countries = serializers.ListField()
    highest_rated = serializers.DictField(allow_null=True)