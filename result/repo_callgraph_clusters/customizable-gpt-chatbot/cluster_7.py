# Cluster 7

class PineconeManager:
    """
    This class is used to manage the Pinecone Indexes
    """

    def __init__(self, api_key, environment):
        pinecone.init(api_key=api_key, environment=environment)

    def list_of_indexes(self):
        try:
            pinecone_index_list = pinecone.list_indexes()
            print('List of Pinecone Indexes: ')
            print(pinecone_index_list)
            print('____________________________________________________')
            return pinecone_index_list
        except Exception as e:
            print('Error in listing the Pinecone Indexes: ', e)
            print('____________________________________________________')
            raise Exception('Error in listing the Pinecone Indexes: ', e)

    def create_index(self, index_name, dimension, metric):
        pinecone.create_index(name=index_name, dimension=dimension, metric=metric)

    def delete_index(self, index_name):
        pinecone.delete_index(index_name)

def list_of_indexes(self):
    try:
        pinecone_index_list = pinecone.list_indexes()
        print('List of Pinecone Indexes: ')
        print(pinecone_index_list)
        print('____________________________________________________')
        return pinecone_index_list
    except Exception as e:
        print('Error in listing the Pinecone Indexes: ', e)
        print('____________________________________________________')
        raise Exception('Error in listing the Pinecone Indexes: ', e)

class ConversationListCreate(generics.ListCreateAPIView):
    """
    List and create conversations.
    """
    serializer_class = ConversationSerializer

    def get_queryset(self):
        return Conversation.objects.filter(user=self.request.user).order_by('created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

def get_queryset(self):
    return Conversation.objects.filter(user=self.request.user).order_by('created_at')

class ConversationDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, and delete a specific conversation.
    """
    serializer_class = ConversationSerializer

    def get_queryset(self):
        return Conversation.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        conversation = self.get_object()
        if conversation.user != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return super().delete(request, *args, **kwargs)

def get_queryset(self):
    return Conversation.objects.filter(user=self.request.user)

class MessageList(generics.ListAPIView):
    """
    List messages in a conversation.
    """
    serializer_class = MessageSerializer
    pagination_class = LastMessagesPagination

    def get_queryset(self):
        conversation = get_object_or_404(Conversation, id=self.kwargs['conversation_id'], user=self.request.user)
        return Message.objects.filter(conversation=conversation).select_related('conversation')

def get_queryset(self):
    conversation = get_object_or_404(Conversation, id=self.kwargs['conversation_id'], user=self.request.user)
    return Message.objects.filter(conversation=conversation).select_related('conversation')

class MessageCreate(generics.CreateAPIView):
    """
    Create a message in a conversation.
    """
    serializer_class = MessageSerializer

    def perform_create(self, serializer):
        conversation = get_object_or_404(Conversation, id=self.kwargs['conversation_id'], user=self.request.user)
        serializer.save(conversation=conversation, is_from_user=True)
        messages = Message.objects.filter(conversation=conversation).order_by('-created_at')[:10][::-1]
        message_list = []
        for msg in messages:
            if msg.is_from_user:
                message_list.append({'role': 'user', 'content': msg.content})
            else:
                message_list.append({'role': 'assistant', 'content': msg.content})
        name_space = User.objects.get(id=self.request.user.id).username
        from site_settings.models import SiteSetting
        try:
            system_prompt_obj = SiteSetting.objects.first()
            system_prompt = system_prompt_obj.prompt
        except Exception as e:
            print(str(e))
            system_prompt = 'You are sonic you can do anything you want.'
        task = send_gpt_request.apply_async(args=(message_list, name_space, system_prompt))
        print(message_list)
        response = task.get()
        return [response, conversation.id, messages[0].id]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        response_list = self.perform_create(serializer)
        assistant_response = response_list[0]
        conversation_id = response_list[1]
        last_user_message_id = response_list[2]
        try:
            message = Message(conversation_id=conversation_id, content=assistant_response, is_from_user=False, in_reply_to_id=last_user_message_id)
            message.save()
        except ObjectDoesNotExist:
            error = f'Conversation with id {conversation_id} does not exist'
            Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_mgs = str(e)
            error = f'Failed to save GPT-3 response as a message: {error_mgs}'
            Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
        headers = self.get_success_headers(serializer.data)
        return Response({'response': assistant_response}, status=status.HTTP_200_OK, headers=headers)

def perform_create(self, serializer):
    conversation = get_object_or_404(Conversation, id=self.kwargs['conversation_id'], user=self.request.user)
    serializer.save(conversation=conversation, is_from_user=True)
    messages = Message.objects.filter(conversation=conversation).order_by('-created_at')[:10][::-1]
    message_list = []
    for msg in messages:
        if msg.is_from_user:
            message_list.append({'role': 'user', 'content': msg.content})
        else:
            message_list.append({'role': 'assistant', 'content': msg.content})
    name_space = User.objects.get(id=self.request.user.id).username
    from site_settings.models import SiteSetting
    try:
        system_prompt_obj = SiteSetting.objects.first()
        system_prompt = system_prompt_obj.prompt
    except Exception as e:
        print(str(e))
        system_prompt = 'You are sonic you can do anything you want.'
    task = send_gpt_request.apply_async(args=(message_list, name_space, system_prompt))
    print(message_list)
    response = task.get()
    return [response, conversation.id, messages[0].id]

