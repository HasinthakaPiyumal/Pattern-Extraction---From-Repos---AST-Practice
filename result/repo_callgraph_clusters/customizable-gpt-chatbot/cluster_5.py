# Cluster 5

class ConversationListCreate(generics.ListCreateAPIView):
    """
    List and create conversations.
    """
    serializer_class = ConversationSerializer

    def get_queryset(self):
        return Conversation.objects.filter(user=self.request.user).order_by('created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

def perform_create(self, serializer):
    serializer.save(user=self.request.user)

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

def delete(self, request, *args, **kwargs):
    conversation = self.get_object()
    if conversation.user != request.user:
        return Response(status=status.HTTP_403_FORBIDDEN)
    return super().delete(request, *args, **kwargs)

class ConversationArchive(APIView):
    """
    Archive a conversation.
    """

    def patch(self, request, pk):
        conversation = get_object_or_404(Conversation, id=pk, user=request.user)
        if conversation.archive:
            conversation.archive = False
            conversation.save()
            return Response({'message': 'remove from archive'}, status=status.HTTP_200_OK)
        else:
            conversation.archive = True
            conversation.save()
            return Response({'message': 'add to archive'}, status=status.HTTP_200_OK)

def patch(self, request, pk):
    conversation = get_object_or_404(Conversation, id=pk, user=request.user)
    if conversation.archive:
        conversation.archive = False
        conversation.save()
        return Response({'message': 'remove from archive'}, status=status.HTTP_200_OK)
    else:
        conversation.archive = True
        conversation.save()
        return Response({'message': 'add to archive'}, status=status.HTTP_200_OK)

class ConversationFavourite(APIView):
    """
    Favourite a conversation.
    """

    def patch(self, request, pk):
        conversation = get_object_or_404(Conversation, id=pk, user=request.user)
        if conversation.favourite:
            conversation.favourite = False
            conversation.save()
            return Response({'message': 'remove from favourite'}, status=status.HTTP_200_OK)
        else:
            conversation.favourite = True
            conversation.save()
            return Response({'message': 'add to favourite'}, status=status.HTTP_200_OK)

def patch(self, request, pk):
    conversation = get_object_or_404(Conversation, id=pk, user=request.user)
    if conversation.favourite:
        conversation.favourite = False
        conversation.save()
        return Response({'message': 'remove from favourite'}, status=status.HTTP_200_OK)
    else:
        conversation.favourite = True
        conversation.save()
        return Response({'message': 'add to favourite'}, status=status.HTTP_200_OK)

class ConversationDelete(APIView):
    """
    Delete a conversation.
    """

    def delete(self, request, pk):
        conversation = get_object_or_404(Conversation, id=pk, user=request.user)
        conversation.delete()
        return Response({'message': 'conversation deleted'}, status=status.HTTP_200_OK)

def delete(self, request, pk):
    conversation = get_object_or_404(Conversation, id=pk, user=request.user)
    conversation.delete()
    return Response({'message': 'conversation deleted'}, status=status.HTTP_200_OK)

class ConversationRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    """
    Retrieve View to update or get the title
    """
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    lookup_url_kwarg = 'conversation_id'

    def retrieve(self, request, *args, **kwargs):
        conversation = self.get_object()
        if conversation.title == 'Empty':
            messages = Message.objects.filter(conversation=conversation)
            if messages.exists():
                message_list = []
                for msg in messages:
                    if msg.is_from_user:
                        message_list.append({'role': 'user', 'content': msg.content})
                    else:
                        message_list.append({'role': 'assistant', 'content': msg.content})
                task = generate_title_request.apply_async(args=(message_list,))
                my_title = task.get()
                my_title = my_title[:30]
                conversation.title = my_title
                conversation.save()
                serializer = self.get_serializer(conversation)
                return Response(serializer.data)
            else:
                return Response({'message': 'No messages in conversation.'}, status=status.HTTP_204_NO_CONTENT)
        else:
            serializer = self.get_serializer(conversation)
            return Response(serializer.data)

def retrieve(self, request, *args, **kwargs):
    conversation = self.get_object()
    if conversation.title == 'Empty':
        messages = Message.objects.filter(conversation=conversation)
        if messages.exists():
            message_list = []
            for msg in messages:
                if msg.is_from_user:
                    message_list.append({'role': 'user', 'content': msg.content})
                else:
                    message_list.append({'role': 'assistant', 'content': msg.content})
            task = generate_title_request.apply_async(args=(message_list,))
            my_title = task.get()
            my_title = my_title[:30]
            conversation.title = my_title
            conversation.save()
            serializer = self.get_serializer(conversation)
            return Response(serializer.data)
        else:
            return Response({'message': 'No messages in conversation.'}, status=status.HTTP_204_NO_CONTENT)
    else:
        serializer = self.get_serializer(conversation)
        return Response(serializer.data)

class GPT3TaskStatus(APIView):
    """
    Check the status of a GPT task and return the result if it's ready.
    """

    def get(self, request, task_id, *args, **kwargs):
        task = AsyncResult(task_id)
        if task.ready():
            response = task.result
            return Response({'status': 'READY', 'response': response})
        else:
            return Response({'status': 'PENDING'})

def get(self, request, task_id, *args, **kwargs):
    task = AsyncResult(task_id)
    if task.ready():
        response = task.result
        return Response({'status': 'READY', 'response': response})
    else:
        return Response({'status': 'PENDING'})

class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    View for user profile retrieval and update.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def perform_update(self, serializer):
        user = serializer.save()
        if 'new_password' in self.request.data:
            new_password = self.request.data['new_password']
            user.set_password(new_password)
            user.save()
            subject = 'Password Changed'
            message = 'Your password has been changed successfully.'
            recipient = user.email
            send_forgot_password_email.delay(subject, message, recipient)

def perform_update(self, serializer):
    user = serializer.save()
    if 'new_password' in self.request.data:
        new_password = self.request.data['new_password']
        user.set_password(new_password)
        user.save()
        subject = 'Password Changed'
        message = 'Your password has been changed successfully.'
        recipient = user.email
        send_forgot_password_email.delay(subject, message, recipient)

class LogoutView(APIView):
    """
    View for user logout.
    """

    def post(self, request, *args, **kwargs):
        token = request.auth
        if token:
            access_token = AccessToken.objects.filter(token=token)
            if access_token.exists():
                access_token.delete()
                return Response({'detail': 'Logout successful'}, status=status.HTTP_200_OK)
        return Response({'detail': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

def post(self, request, *args, **kwargs):
    token = request.auth
    if token:
        access_token = AccessToken.objects.filter(token=token)
        if access_token.exists():
            access_token.delete()
            return Response({'detail': 'Logout successful'}, status=status.HTTP_200_OK)
    return Response({'detail': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

