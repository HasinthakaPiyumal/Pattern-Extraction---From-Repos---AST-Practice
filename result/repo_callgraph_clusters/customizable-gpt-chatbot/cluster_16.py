# Cluster 16

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

def time_since(dt):
    """
    Returns string representing "time since" e.g.
    """
    now = datetime.now(timezone.utc)
    diff = now - dt
    seconds = diff.total_seconds()
    minutes = int(seconds // 60)
    hours = int(minutes // 60)
    days = int(hours // 24)
    months = int(days // 30)
    years = int(days // 365)
    if years > 0:
        return f'{years} year{('s' if years > 1 else '')} ago'
    elif months > 0:
        return f'{months} month{('s' if months > 1 else '')} ago'
    elif days > 0:
        return f'{days} day{('s' if days > 1 else '')} ago'
    elif hours > 0:
        return f'{hours} hour{('s' if hours > 1 else '')} ago'
    elif minutes > 0:
        return f'{minutes} minute{('s' if minutes > 1 else '')} ago'
    else:
        return f'{int(seconds)} second{('s' if seconds > 1 else '')} ago'

class LoginView(APIView):
    """
    Login API view.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        client_id = request.data.get('client_id')
        if username:
            if password is None or client_id is None:
                return Response({'error': 'username, password and client_id are required'}, status=status.HTTP_400_BAD_REQUEST)
            user = authenticate(request, username=username, password=password)
        else:
            if email is None or password is None or client_id is None:
                return Response({'error': 'email, password and client_id are required'}, status=status.HTTP_400_BAD_REQUEST)
            user = authenticate(request, username=email, password=password)
        if user is None:
            return Response({'error': 'Invalid email or password'}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            app = Application.objects.get(client_id=client_id)
        except Application.DoesNotExist:
            return Response({'error': 'Invalid client_id'}, status=status.HTTP_401_UNAUTHORIZED)
        access_token = generate_token()
        refresh_token = generate_token()
        expires_in = timedelta(seconds=oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS)
        expires = timezone.now() + expires_in
        AccessToken.objects.create(user=user, token=access_token, application=app, scope=oauth2_settings.DEFAULT_SCOPES, expires=timezone.now() + timedelta(seconds=oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS))
        RefreshToken.objects.create(user=user, token=refresh_token, application=app, access_token=AccessToken.objects.get(token=access_token))
        context = {'access_token': access_token, 'refresh_token': refresh_token}
        return Response(context, status=status.HTTP_200_OK)

def post(self, request, *args, **kwargs):
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    client_id = request.data.get('client_id')
    if username:
        if password is None or client_id is None:
            return Response({'error': 'username, password and client_id are required'}, status=status.HTTP_400_BAD_REQUEST)
        user = authenticate(request, username=username, password=password)
    else:
        if email is None or password is None or client_id is None:
            return Response({'error': 'email, password and client_id are required'}, status=status.HTTP_400_BAD_REQUEST)
        user = authenticate(request, username=email, password=password)
    if user is None:
        return Response({'error': 'Invalid email or password'}, status=status.HTTP_401_UNAUTHORIZED)
    try:
        app = Application.objects.get(client_id=client_id)
    except Application.DoesNotExist:
        return Response({'error': 'Invalid client_id'}, status=status.HTTP_401_UNAUTHORIZED)
    access_token = generate_token()
    refresh_token = generate_token()
    expires_in = timedelta(seconds=oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS)
    expires = timezone.now() + expires_in
    AccessToken.objects.create(user=user, token=access_token, application=app, scope=oauth2_settings.DEFAULT_SCOPES, expires=timezone.now() + timedelta(seconds=oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS))
    RefreshToken.objects.create(user=user, token=refresh_token, application=app, access_token=AccessToken.objects.get(token=access_token))
    context = {'access_token': access_token, 'refresh_token': refresh_token}
    return Response(context, status=status.HTTP_200_OK)

class UserRegistrationView(generics.CreateAPIView):
    """
    View for user registration.
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        email = request.data.get('email')
        if User.objects.filter(email=email).exists():
            return Response({'error': 'Email address already exists'}, status=status.HTTP_400_BAD_REQUEST)
        password = request.data.get('password')
        request.data['password'] = make_password(password)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        app = get_object_or_404(Application, name=settings.APPLICATION_NAME)
        access_token = generate_token()
        refresh_token = generate_token()
        AccessToken.objects.create(user=user, token=access_token, application=app, scope=oauth2_settings.DEFAULT_SCOPES, expires=timezone.now() + timedelta(seconds=oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS))
        RefreshToken.objects.create(user=user, token=refresh_token, application=app, access_token=AccessToken.objects.get(token=access_token))
        tokens = {'access_token': access_token, 'refresh_token': refresh_token}
        context = serializer.data.copy()
        context.update(tokens)
        return Response(context, status=status.HTTP_201_CREATED)

def create(self, request, *args, **kwargs):
    email = request.data.get('email')
    if User.objects.filter(email=email).exists():
        return Response({'error': 'Email address already exists'}, status=status.HTTP_400_BAD_REQUEST)
    password = request.data.get('password')
    request.data['password'] = make_password(password)
    serializer = self.get_serializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    app = get_object_or_404(Application, name=settings.APPLICATION_NAME)
    access_token = generate_token()
    refresh_token = generate_token()
    AccessToken.objects.create(user=user, token=access_token, application=app, scope=oauth2_settings.DEFAULT_SCOPES, expires=timezone.now() + timedelta(seconds=oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS))
    RefreshToken.objects.create(user=user, token=refresh_token, application=app, access_token=AccessToken.objects.get(token=access_token))
    tokens = {'access_token': access_token, 'refresh_token': refresh_token}
    context = serializer.data.copy()
    context.update(tokens)
    return Response(context, status=status.HTTP_201_CREATED)

