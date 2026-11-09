from rest_framework import serializers

class CountryRankingItemSerializer(serializers.Serializer):
    country = serializers.CharField()
    users_count = serializers.IntegerField()
    total_solved = serializers.IntegerField()
    avg_rating = serializers.FloatField()
    top_user = serializers.CharField(allow_null=True)