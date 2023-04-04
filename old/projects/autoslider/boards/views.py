from django.contrib.auth import get_user_model, login, authenticate, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponseForbidden
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .models import Board
from .forms import BoardCreateForm

import os
import torch
import whisper
from transformers import PreTrainedTokenizerFast, BartForConditionalGeneration
import pytube
from pytube import YouTube
from pydub import AudioSegment
from moviepy.editor import *


# Create your views here.

# 새 보드 만들기
# def board_create(request):
#     if request.method == 'POST':
#         form = BoardForm(request.POST, request.FILES)
#         if form.is_valid():
#             board = form.save(commit=False)
#             board.user_id = request.user
#             board.save()
#             return redirect('board_detail', pk=board.pk)
#     else:
#         form = BoardForm()
#     return render(request, 'boards/board_detail.html', {'form': form})

# 보드 생성
# class BoardCreateView(CreateView):
#     model = Board
#     form_class = BoardCreateForm
#     template_name = 'boards/board_form.html'
#     success_url = reverse_lazy('board_list')

#     def form_valid(self, form):
#         form.instance.user_id = self.request.user
#         return super().form_valid(form)


# 상세 보드
class BoardDetailView(LoginRequiredMixin, DetailView):
    model = Board
    template_name = 'boards/board_detail.html'
    form_class = BoardCreateForm
    # success_url = reverse_lazy('board_detail')

    # 로그인한 사용자와 요약 작성자가 일치하지 않으면 에러 페이지 반환
    def get_object(self, queryset=None):
        obj = get_object_or_404(Board, id=self.kwargs['pk'])
        if obj.user_id != self.request.user:
            raise HttpResponseForbidden("You are not allowed to view this summary.")
        return obj

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('boards:board_detail', kwargs={'pk': self.object.pk})


# BoardListView
# 모든 보드 목록
class BoardListView(LoginRequiredMixin, ListView):  # LoginRequiredMixin을 상속받아 로그인한 사용자만 접근할 수 있도록 설정
    model = Board
    template_name = 'boards/board_list.html'
    def get_queryset(self):
        # Filter the queryset to include only boards created by the current user
        return Board.objects.filter(user_id=self.request.user.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['board_list'] = self.get_queryset()
        return context


# 즐겨찾기 인 경우 override함.
class FavoriteBoardListView(BoardListView):
    def get_queryset(self):
        return super().get_queryset().filter(favorite=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['favorite_board_list'] = self.get_queryset()
        return context



# 영상 업로드 & youtube 다운 & 긴 텍스트 요약 처리

# chocolatey 로 ffmpge 설치 했으나 경로 지정 필요
def get_ffmpeg_path():
    search_paths = [
        r'C:\Program Files\ffmpeg\bin',
        r'C:\Program Files (x86)\ffmpeg\bin',
        r'C:\ProgramData\chocolatey\bin',
    ]

    for path in search_paths:
        ffmpeg_path = os.path.join(path, 'ffmpeg.exe')
        if os.path.exists(ffmpeg_path):
            return ffmpeg_path

    return None

ffmpeg_path = get_ffmpeg_path()
if ffmpeg_path:
    os.environ["PATH"] = ffmpeg_path + os.pathsep + os.environ["PATH"]
    os.environ["FFMPEG_BINARY"] = ffmpeg_path # FFmpeg 경로 설정
    AudioSegment.ffmpeg = ffmpeg_path  # pydub 패키지가 ffmpeg.exe 경로를 인식하도록 함.
else:
    print("FFmpeg not found in any search path")


tokenizer = PreTrainedTokenizerFast.from_pretrained('digit82/kobart-summarization')
model = BartForConditionalGeneration.from_pretrained('digit82/kobart-summarization')


# 텍스트 분리
def split_text(text, max_length):
    words = text.split()
    parts = []
    current_part = []

    for word in words:
        current_part.append(word)
        if len(tokenizer.encode(" ".join(current_part))) > max_length:
            current_part.pop()
            parts.append(" ".join(current_part))
            current_part = [word]

    if current_part:
        parts.append(" ".join(current_part))

    return parts


# 텍스트 요약
def summarize(text):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    input_ids = tokenizer.encode(text)
    input_ids = torch.tensor(input_ids).unsqueeze(0).to(device)

    output = model.generate(input_ids, eos_token_id=1, max_length=512, num_beams=5, no_repeat_ngram_size=1)
    return tokenizer.decode(output[0], skip_special_tokens=True)


# 전문 텍스트 요약
def summarize_long_text(text):
    max_input_length = 1000  # 몇 개의 여유 토큰을 남겨두기 위해 1026보다 작은 값을 사용합니다.
    text_parts = split_text(text, max_input_length)

    summarized_parts = []
    for part in text_parts:
        summary = summarize(part)
        summarized_parts.append(summary)

    return " ".join(summarized_parts)


# timestamp track -> timeline 생성
def create_timelined_text(segments):
    timelined_text = []
    for segment in segments:
        segment_start = round(segment['start'], 2)
        segment_text = segment['text']
        segment_t = round(segment_start, 2)
        segment_text_with_t = f'<span t="{segment_t}" data-lexical-text="true" style="" onclick="seekToTimestamp(\'{segment_t}\');">{segment_text}</span>'
        timelined_text.append(segment_text_with_t)
    return "\n".join(timelined_text)


# 요약 종합
class BoardCreateView(LoginRequiredMixin, CreateView):
    def post(self, request):
        form = BoardCreateForm(request.POST, request.FILES)
        if form.is_valid():
            board = form.save(commit=False)
            # board.user = request.user
            # board.user_id = self.request.user.id
            form.instance.user_id = self.request.user

            # Handle text summary
            input_text = form.cleaned_data['input_text']
            if input_text:
                # Run deep learning model
                original_text = input_text
                # Use a function to summarize long text
                summary_text = summarize_long_text(original_text)
                timeline_text = ""
                board.summary_text = summary_text
                board.timeline_text = timeline_text
                board.result = ""  # assuming there is no result for text input
                board.save()
                # Define the URL to redirect to
                redirect_url = reverse('boards:board_detail', args=[board.id])
                # return JsonResponse({'status': 'success', 'redirect_url': redirect_url})
                # return redirect_url
                return redirect(redirect_url)

            # Video file processing
            input_video = form.cleaned_data['input_video']
            if input_video:
                # Convert to image
                # Run deep learning model
                # 파일 업로드가 있는 경우
                file_name = default_storage.save(input_video.name, ContentFile(input_video.read()))
                file_path = default_storage.path(file_name)

                #whisper로 자막화 하는 코드
                device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                whispermodel = whisper.load_model("small", device=device)
                result = whispermodel.transcribe(file_path)
                original_text = result["text"]
                segments = result["segments"]

                timeline_text = create_timelined_text(segments)
                summary_text = summarize_long_text(original_text)
                summary_file = input_video

                # 업로드 된 파일 삭제
                default_storage.delete(file_path)
                # Save results to board instance
                board.save()
                redirect_url = reverse('boards:board_detail', args=[board.id])
                # return JsonResponse({'status': 'success', 'redirect_url': redirect_url})
                # return redirect_url
                return redirect(redirect_url)

            # Handle YouTube links
            input_youtube = form.cleaned_data['input_youtube']
            if input_youtube:
                # Run deep learning model
                youtube = pytube.YouTube(input_youtube)
                video = youtube.streams.first()
                video.download()

                device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                whispermodel = whisper.load_model("small", device=device) # medium
                # medium 은 OutOfMemoryError at /new/ 나옴
                # CUDA out of memory. Tried to allocate 20.00 MiB (GPU 0; 4.00 GiB total capacity; 3.46 GiB already allocated; 0 bytes free; 3.47 GiB reserved in total by PyTorch) If reserved memory is >> allocated memory try setting max_split_size_mb to avoid fragmentation.  See documentation for Memory Management and PYTORCH_CUDA_ALLOC_CONF
                result = whispermodel.transcribe(video.default_filename)
                original_text = result["text"]
                segments = result["segments"]

                timeline_text = create_timelined_text(segments)
                summary_text = summarize_long_text(original_text)
                board.summary_text = summary_text
                board.timeline_text = timeline_text
                board.result = result
                board.save()

                os.remove(video.default_filename)
                redirect_url = reverse('boards:board_detail', args=[board.id])
                # return JsonResponse({'status': 'success', 'redirect_url': redirect_url})
                # return redirect_url
                return redirect(redirect_url)

        # return JsonResponse({'status': 'fail'})
        error_message = {'error': 'Invalid input values'}
        return JsonResponse(error_message, status=400)
