from rest_framework import serializers

class SchoolRankingItemSerializer(serializers.Serializer):
    school = serializers.CharField()
    students_count = serializers.IntegerField()
    total_solved = serializers.IntegerField()
    avg_rating = serializers.FloatField()
    top_student = serializers.CharField(allow_null=True)