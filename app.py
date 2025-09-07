import streamlit as st
import subprocess
import os

# --- 유틸 함수 ---
def time_to_seconds(time_str):
    parts = time_str.split(':')
    hours = int(parts[0]) if len(parts) > 2 else 0
    minutes = int(parts[-2]) if len(parts) > 1 else 0
    seconds = int(parts[-1])
    return hours * 3600 + minutes * 60 + seconds

def calculate_duration(start_time, end_time):
    start_seconds = time_to_seconds(start_time)
    end_seconds = time_to_seconds(end_time)
    duration_seconds = end_seconds - start_seconds

    if duration_seconds <= 0:
        return None

    hours = duration_seconds // 3600
    minutes = (duration_seconds % 3600) // 60
    seconds = duration_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def download_m3u8_segment(m3u8_url, start_time, end_time, filename):
    """FFmpeg를 사용하여 M3U8에서 특정 시간대 추출"""
    current_dir = os.getcwd()
    output_path = os.path.join(current_dir, f"{filename}.mp4")

    duration = calculate_duration(start_time, end_time)
    if duration is None:
        return False, "❌ 종료 시간이 시작 시간보다 빠릅니다.", None

    ffmpeg_cmd = [
        "ffmpeg",
        "-ss", start_time,
        "-i", m3u8_url,
        "-t", duration,
        "-c", "copy",
        "-avoid_negative_ts", "make_zero",
        "-y",  # 기존 파일 덮어쓰기
        output_path
    ]

    try:
        result = subprocess.run(
            ffmpeg_cmd,
            capture_output=True,
            text=True,
            check=True
        )
        return True, output_path, output_path
    except subprocess.CalledProcessError as e:
        return False, e.stderr, None
    except FileNotFoundError:
        return False, "FFmpeg가 설치되지 않았거나 PATH에 추가되지 않았습니다.", None


# --- Streamlit UI ---
st.set_page_config(page_title="M3U8 다중 시간대 다운로더", layout="wide")
st.title("🎬 M3U8 다중 시간대 다운로더 (Streamlit)")

# M3U8 주소 입력
url = st.text_input("M3U8 주소 입력")

# 섹션 입력 (다중)
st.subheader("🎯 추출할 섹션 설정")
num_sections = st.number_input("추출할 섹션 개수", min_value=1, max_value=10, value=1, step=1)

sections = []
for i in range(num_sections):
    st.markdown(f"#### 섹션 {i+1}")
    cols = st.columns(2)

    with cols[0]:
        start_h = st.number_input(f"시작 시간 (시)", min_value=0, max_value=23, value=0, key=f"sh{i}")
        start_m = st.number_input(f"시작 시간 (분)", min_value=0, max_value=59, value=0, key=f"sm{i}")
        start_s = st.number_input(f"시작 시간 (초)", min_value=0, max_value=59, value=0, key=f"ss{i}")

    with cols[1]:
        end_h = st.number_input(f"종료 시간 (시)", min_value=0, max_value=23, value=0, key=f"eh{i}")
        end_m = st.number_input(f"종료 시간 (분)", min_value=0, max_value=59, value=0, key=f"em{i}")
        end_s = st.number_input(f"종료 시간 (초)", min_value=0, max_value=59, value=0, key=f"es{i}")

    filename = st.text_input(f"파일명 (확장자 제외)", value=f"output_{i+1}", key=f"fn{i}")

    start_time = f"{start_h:02d}:{start_m:02d}:{start_s:02d}"
    end_time = f"{end_h:02d}:{end_m:02d}:{end_s:02d}"

    sections.append({
        "section_num": i+1,
        "start_time": start_time,
        "end_time": end_time,
        "filename": filename
    })

# 미리보기
st.subheader("🔍 미리보기")
if url:
    for section in sections:
        duration = calculate_duration(section["start_time"], section["end_time"])
        st.markdown(
            f"""
            **영상 {section['section_num']}**
            - 시작: {section['start_time']}
            - 종료: {section['end_time']}
            - 길이: {duration if duration else "❌ 잘못된 구간"}
            - 저장: {section['filename']}.mp4
            """
        )

# 추출 버튼
if st.button("🚀 추출하기"):
    if not url.strip():
        st.error("❌ M3U8 주소를 입력해주세요.")
    else:
        for section in sections:
            with st.spinner(f"영상 {section['section_num']} 추출 중..."):
                success, result, file_path = download_m3u8_segment(
                    url,
                    section["start_time"],
                    section["end_time"],
                    section["filename"]
                )
                if success and file_path:
                    st.success(f"✅ 영상 {section['section_num']} 추출 완료! → {file_path}")
                    # 다운로드 버튼 추가
                    with open(file_path, "rb") as f:
                        st.download_button(
                            label=f"⬇️ 영상 {section['section_num']} 다운로드",
                            data=f,
                            file_name=os.path.basename(file_path),
                            mime="video/mp4"
                        )
                else:
                    st.error(f"❌ 영상 {section['section_num']} 추출 실패: {result}")
