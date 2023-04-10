# 통합본

- AutoSlider의 전체 통합된 파일 입니다.
!![AutoSlider](https://user-images.githubusercontent.com/102719063/230900543-00d26481-3fac-4a2a-bde9-a7c3306033ff.png)
- AutoSlider 프로젝트는 점프 투 장고(https://wikidocs.net/book/4223) 의 환경 설정을 기반으로 진행하여, venvs과 projects 라는 디렉토리로 분류하였고, venvs의 `pip`의 목록은 에서 확인하실 수 있습니다.
- requirements.txt : `pip` 단으로 필요한 버전에 대해서.
    - 다만 내용 중에서
        1. torch==2.0.0+cu118
        2. torchaudio==2.0.1+cu118
        3. torchvision==0.15.1+cu118
    - 위 3개의 경우 <br>```pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118```<br> 를 통해서 개별로 설치된 것입니다.
- projects/ : 실질 적용되는 프로젝트 코드

# 2023-04-10 으로 발표까지 완료.

# 시연 연상
https://user-images.githubusercontent.com/102719063/230899102-b5405b79-ae6a-4abf-ab59-cbb4098b6baf.mp4

