# Cluster 19

class ConversationSerializer(serializers.ModelSerializer):
    """
    Conversation serializer.
    """
    messages = MessageSerializer(many=True, read_only=True)
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'title', 'favourite', 'archive', 'created_at', 'messages']

    def get_created_at(self, obj):
        return time_since(obj.created_at)

def get_created_at(self, obj):
    return time_since(obj.created_at)

