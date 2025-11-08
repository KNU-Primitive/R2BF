import streamlit as st
import google.generativeai as genai
import time
import uuid
import datetime

# ----------------------------------------------------------------------
# 0. 앱 설정 및 세션 상태 초기화
# ----------------------------------------------------------------------
st.set_page_config(layout="wide", page_title="AI 거버넌스 대시보드 (Final Ver)")

# 'R2BF 인증서' DB
if "certificate_db" not in st.session_state:
    st.session_state.certificate_db = {}

    # --- 예시 데이터 ---
    example_id = "CERT-2025-001"
    example_time = (datetime.datetime.now() - datetime.timedelta(days=1)).isoformat()
    st.session_state.certificate_db[example_id] = {
        "cert_id": example_id,
        "requester_id": "김감사 (AI 윤리팀)",
        "operator_id": None,
        "approver_id": None,
        "completion_date": None,
        "content": {
            "model_name": "신용평가 AI 모델",
            "deleted_data": "구(舊) 주소 데이터셋 (편향성 원인)",
            "replacement_data": None
        },
        "log": [
            {"timestamp": example_time, "status": "Pending_Forget", "actor": "김감사 (AI 윤리팀)", "message": "신규 '잊힘' 요청 발행"}
        ],
        "current_status": "Pending_Forget",
        "internal_ai_suggestion": None
    }
    # --- ---

# API 키 및 모델 상태
if "api_model" not in st.session_state:
    st.session_state.api_model = None

# --- [수정] 사용할 모델을 세션 상태에 추가 ---
if "selected_model" not in st.session_state:
    st.session_state.selected_model = "gemini-2.0-flash"  # 기본값


# --- ---

# ----------------------------------------------------------------------
# 1. 헬퍼 함수 정의
# ----------------------------------------------------------------------

def get_ai_replacement(api_model, deleted_data_text, model_name):
    """
    [장면 4] MLOps가 '대체' 알고리즘 수행 시 호출하는 AI 생성 함수
    """
    prompt = f"""
    [배경]: AI 모델 '{model_name}'에서 편향성 원인 데이터인 '{deleted_data_text}'가 '잊힘(Unlearn)' 처리되었습니다.
    [작업]: 이로 인해 발생한 지식 공백(Gap)을 채울, 윤리적이고 공정한 '대체 지식' 또는 '정책'을 생성하세요.

    [규칙]:
    1. 삭제된 데이터의 편향성(예: 특정 지역)을 암시하는 내용을 절대 포함하지 마세요.
    2. "모든 지역의 데이터는 공정한 기준에 따라 처리됩니다." 또는 "신용 평가는 거주지가 아닌, 개인의 신용 기록을 기반으로 합니다."와 같이 중립적이고 윤리적인 원칙을 생성하세요.

    [생성된 대체 지식/정책]:
    """
    try:
        generation_config = genai.GenerationConfig(temperature=0.3)
        response = api_model.generate_content(prompt, generation_config=generation_config)
        return response.text.strip()
    except Exception as e:
        return f"[AI 생성 실패] {str(e)}"


def get_current_time_str():
    """현재 시간을 ISO 형식의 문자열로 반환"""
    return datetime.datetime.now().isoformat()


# --- 콜백 함수 (각 장면의 버튼 클릭 시 작동) ---

def submit_request_callback():
    """
    [장면 1: 김감사] 삭제 요청 (인증서 발행)
    """
    model_name = st.session_state.req_model_name
    data_to_delete = st.session_state.req_dataset
    requester_name = "김감사 (AI 윤리팀)"

    if model_name and data_to_delete:
        cert_id = f"CERT-2025-{str(uuid.uuid4())[:3].upper()}"

        st.session_state.certificate_db[cert_id] = {
            "cert_id": cert_id,
            "requester_id": requester_name,
            "operator_id": None,
            "approver_id": None,
            "completion_date": None,
            "content": {
                "model_name": model_name,
                "deleted_data": data_to_delete,
                "replacement_data": None
            },
            "log": [
                {"timestamp": get_current_time_str(), "status": "Pending_Forget", "actor": requester_name,
                 "message": "신규 '잊힘' 요청 발행"}
            ],
            "current_status": "Pending_Forget",
            "internal_ai_suggestion": None
        }
        st.session_state.req_model_name = ""
        st.session_state.req_dataset = ""
        st.toast(f"✅ 인증서 [{cert_id}]가 발행되었습니다. (MLOps '잊힘' 대기)")


def run_forgetting_callback(cert_id):
    """
    [장면 2: 박엔진] '잊힘' 수행 -> R2BF에 '잊힘' 승인 요청
    """
    cert = st.session_state.certificate_db[cert_id]
    operator_name = "박엔진 (MLOps팀)"

    cert["operator_id"] = operator_name
    cert["current_status"] = "Forgetting_In_Progress"
    st.toast(f"[{cert_id}] '잊힘' 알고리즘을 수행합니다... (시뮬레이션)")

    time.sleep(1.5)

    cert["current_status"] = "Pending_Forget_Approval"
    cert["log"].append(
        {"timestamp": get_current_time_str(), "status": "Pending_Forget_Approval", "actor": operator_name,
         "message": "'잊힘' 수행 완료. R2BF '잊힘' 승인 대기"})


def approve_forget_callback(cert_id):
    """
    [장면 3: R2BF] '잊힘' 승인 -> MLOps에 '대체 작업' 요청
    """
    cert = st.session_state.certificate_db[cert_id]
    approver_name = "R2BF 부서"

    cert["current_status"] = "Pending_Substitute"
    cert["approver_id"] = approver_name
    cert["log"].append({"timestamp": get_current_time_str(), "status": "Pending_Substitute", "actor": approver_name,
                        "message": "'잊힘' 승인 완료. MLOps '대체' 작업 대기."})
    st.toast(f"[{cert_id}] '잊힘' 승인 완료. MLOps에 '대체' 작업을 요청합니다.")


def reject_forget_callback(cert_id):
    """
    [장면 3: R2BF] '잊힘' 거부 -> MLOps에 재작업 요청
    """
    reason_key = f"reject_reason_forget_{cert_id}"
    reason = st.session_state.get(reason_key, "").strip()

    if not reason:
        st.warning(f"[{cert_id}] 거부 사유를 반드시 작성해야 합니다.")
        return

    cert = st.session_state.certificate_db[cert_id]
    approver_name = "R2BF 부서"

    cert["current_status"] = "Pending_Forget"
    cert["operator_id"] = None
    cert["log"].append({"timestamp": get_current_time_str(), "status": "Pending_Forget", "actor": approver_name,
                        "message": f"'잊힘' 거부 (사유: {reason}). MLOps 재작업 요청."})

    st.session_state[reason_key] = ""
    st.toast(f"[{cert_id}] '잊힘'을 거부하고 MLOps에 재작업을 요청했습니다.")


def run_substitute_callback(cert_id):
    """
    [장면 4: 박엔진] '대체' 수행 (AI 생성 포함) -> MLOps의 자체 검토 대기
    """
    if not st.session_state.api_model:
        st.error("API 모델이 설정되지 않았습니다. API 키를 먼저 입력하세요.")
        return

    cert = st.session_state.certificate_db[cert_id]
    operator_name = "박엔진 (MLOps팀)"

    cert["current_status"] = "Substituting_In_Progress"
    st.toast(f"[{cert_id}] '대체' 알고리즘을 수행합니다... (AI 제안 생성 중)")

    deleted_data = cert["content"]["deleted_data"]
    model_name = cert["content"]["model_name"]
    ai_replacement = get_ai_replacement(st.session_state.api_model, deleted_data, model_name)
    time.sleep(1.0)

    cert["internal_ai_suggestion"] = ai_replacement
    st.session_state[f"mlops_edit_{cert_id}"] = ai_replacement

    cert["current_status"] = "Pending_Substitute_Review_MLOps"
    cert["log"].append(
        {"timestamp": get_current_time_str(), "status": "Pending_Substitute_Review_MLOps", "actor": operator_name,
         "message": "'대체' AI 제안 생성 완료. MLOps 자체 검토 대기"})


def regenerate_ai_suggestion_mlops_callback(cert_id):
    """
    [장면 4: 박엔진] 'AI 재탐색' 요청
    """
    if not st.session_state.api_model:
        st.error("API 모델이 설정되지 않았습니다.")
        return

    cert = st.session_state.certificate_db[cert_id]
    st.toast(f"[{cert_id}] AI 재탐색을 요청합니다...")

    deleted_data = cert["content"]["deleted_data"]
    model_name = cert["content"]["model_name"]
    ai_replacement = get_ai_replacement(st.session_state.api_model, deleted_data, model_name)

    cert["internal_ai_suggestion"] = ai_replacement
    st.session_state[f"mlops_edit_{cert_id}"] = ai_replacement

    cert["log"].append(
        {"timestamp": get_current_time_str(), "status": "Pending_Substitute_Review_MLOps", "actor": "박엔진 (MLOps팀)",
         "message": "MLOps AI 재탐색 수행"})


def send_substitute_to_r2bf_callback(cert_id):
    """
    [장면 4: 박엔진] 검토 완료 후 'R2BF에 승인 요청' 전송
    """
    cert = st.session_state.certificate_db[cert_id]

    edited_text = st.session_state[f"mlops_edit_{cert_id}"]
    cert["internal_ai_suggestion"] = edited_text

    cert["current_status"] = "Pending_Substitute_Approval"
    cert["log"].append(
        {"timestamp": get_current_time_str(), "status": "Pending_Substitute_Approval", "actor": "박엔진 (MLOps팀)",
         "message": "MLOps '대체(안)' 수정/검토 완료. R2BF 최종 승인 대기"})

    if f"mlops_edit_{cert_id}" in st.session_state:
        del st.session_state[f"mlops_edit_{cert_id}"]

    st.toast(f"[{cert_id}] '대체(안)'을 R2BF 부서에 승인 요청했습니다.")


def approve_substitute_callback(cert_id):
    """
    [장면 5: R2BF] '대체' 최종 승인 -> 인증서 완료 처리
    """
    cert = st.session_state.certificate_db[cert_id]
    approver_name = "R2BF 부서"

    final_replacement_text = cert['internal_ai_suggestion']

    cert["content"]["replacement_data"] = final_replacement_text
    cert["approver_id"] = approver_name
    cert["completion_date"] = get_current_time_str()
    cert["current_status"] = "Completed"
    cert["log"].append({"timestamp": cert["completion_date"], "status": "Completed", "actor": approver_name,
                        "message": "'대체' 및 최종 승인 완료. 인증서 발행."})

    st.toast(f"✅ [{cert_id}] 최종 승인 완료! 인증서가 '완료' 처리되었습니다.")


def reject_substitute_callback(cert_id):
    """
    [장면 5: R2BF] '대체' 거부 -> MLOps '재검토' 요청
    """
    reason_key = f"reject_reason_sub_{cert_id}"
    reason = st.session_state.get(reason_key, "").strip()

    if not reason:
        st.warning(f"[{cert_id}] 거부 사유를 반드시 작성해야 합니다.")
        return

    cert = st.session_state.certificate_db[cert_id]
    approver_name = "R2BF 부서"

    cert["current_status"] = "Pending_Substitute_Review_MLOps"
    st.session_state[f"mlops_edit_{cert_id}"] = cert["internal_ai_suggestion"]

    cert["log"].append(
        {"timestamp": get_current_time_str(), "status": "Pending_Substitute_Review_MLOps", "actor": approver_name,
         "message": f"'대체(안)' 거부 (사유: {reason}). MLOps 재검토 요청."})

    st.session_state[reason_key] = ""
    st.toast(f"[{cert_id}] '대체(안)'을 거부하고 MLOps에 재검토를 요청했습니다.")


# ----------------------------------------------------------------------
# 2. 🛠️ API 키 설정 (사이드바)
# ----------------------------------------------------------------------
with st.sidebar:
    st.title("🎛️ 시스템 설정")
    st.write("AI '대체' 문장 생성을 위해 API 키가 필요합니다.")

    # --- [수정] 모델 선택 드롭다운 추가 ---
    model_options = ["gemini-2.0-flash", "gemini-2.5-flash"]
    st.selectbox(
        "사용할 AI 모델 선택:",
        options=model_options,
        key="selected_model"  # 세션 상태에 'selected_model'로 저장
    )
    # --- ---

    api_key = st.text_input("Google AI API Key:", type="password", key="api_key_input")

    if st.button("API 키 설정"):
        # [수정] 위젯의 키(key)에서 값을 읽어옴
        api_key_value = st.session_state.api_key_input
        selected_model_name = st.session_state.selected_model  # 드롭다운에서 선택된 모델

        if api_key_value:
            try:
                genai.configure(api_key=api_key_value)
                # [수정] 하드코딩된 모델명 대신, 선택된 모델명 사용
                model = genai.GenerativeModel(selected_model_name)

                st.session_state.api_model = model
                # [수정] 성공 메시지에 선택된 모델명 표시
                st.success(f"API 키 설정 및 '{selected_model_name}' 모델 로드 완료!")
            except Exception as e:
                st.session_state.api_model = None
                st.error(f"API 키 오류: {e}")
        else:
            st.warning("API 키를 입력해주세요.")

    if not st.session_state.api_model:
        st.warning("API 키를 설정해야 MLOps팀이 '대체' 작업을 수행할 수 있습니다.")

# ----------------------------------------------------------------------
# 3. 👤 3자 + 1 (조회) 대시보드 (메인 화면)
# ----------------------------------------------------------------------
st.title("🤖 AI 거버넌스 대시보드 (R2BF 프레임워크)")
st.caption(f"현재 시간: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

tab1, tab2, tab3, tab4 = st.tabs([
    "👤 김감사 (AI 윤리팀)",
    "🛠️ 박엔진 (MLOps팀)",
    "🛡️ R2BF 부서 (승인팀)",
    "🗂️ 인증서 조회"
])

# --- [장면 1 & 6] 김감사 (AI 윤리팀) 대시보드 ---
with tab1:
    st.header("👤 김감사 (AI 윤리팀) 대시보드")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("장면 1: 신규 '잊힘' 요청 (인증서 발행)")
        st.markdown("정기 감사에서 발견된 편향성 원인 데이터셋의 '잊힘(Unlearn)'을 요청합니다.")

        with st.form("request_form"):
            st.text_input(
                "AI 모델명:",
                key="req_model_name",
                autocomplete="off"
            )
            st.text_area(
                "삭제 요청 데이터셋 (편향성 원인):",
                key="req_dataset",
                placeholder="감사 리포트에 근거한 편향성 원인 데이터셋을 입력하세요."
            )
            submit_button = st.form_submit_button(
                "삭제 요청 (인증서 발행)",
                use_container_width=True,
                type="primary",
                on_click=submit_request_callback
            )

    with col2:
        st.subheader("장면 6: 인증서 처리 현황 (모니터링)")
        st.markdown("내가 요청한 '잊힘' 인증서의 **처리 상태만** 확인합니다.\n\n(상세 내용은 **'🗂️ 인증서 조회'** 탭을 이용하세요.)")

        certs = {k: v for k, v in st.session_state.certificate_db.items() if v['requester_id'] == "김감사 (AI 윤리팀)"}
        if not certs:
            st.info("아직 발행한 인증서가 없습니다.")

        sorted_certs = sorted(certs.values(), key=lambda x: x['log'][0]['timestamp'], reverse=True)

        for cert in sorted_certs:
            status = cert["current_status"]

            if status == "Completed":
                st.success(f"**{cert['cert_id']} (처리 완료)**")
            elif status == "Pending_Forget":
                st.info(f"**{cert['cert_id']} (MLOps '잊힘' 대기)**")
            elif status == "Pending_Forget_Approval":
                st.warning(f"**{cert['cert_id']} (R2BF '잊힘' 승인 대기)**")
            elif status == "Pending_Substitute":
                st.warning(f"**{cert['cert_id']} (MLOps '대체' 작업 대기)**")
            elif status == "Pending_Substitute_Review_MLOps":
                st.warning(f"**{cert['cert_id']} (MLOps '대체(안)' 검토 중)**")
            elif status == "Pending_Substitute_Approval":
                st.warning(f"**{cert['cert_id']} (R2BF '대체' 승인 대기)**")
            else:
                st.info(f"**{cert['cert_id']} (처리 중...)** | 상태: {status}")

# --- [장면 2 & 4] 박엔진 (MLOps팀) 대시보드 ---
with tab2:
    st.header("🛠️ 박엔진 (MLOps팀) 대시보드")

    st.subheader("장면 2: '잊힘' (Unlearn) 작업 큐")
    st.markdown(
        "AI 윤리팀에서 요청한 '잊힘' 작업을 수행하고, R2BF에 '잊힘' 승인을 요청합니다.\n\n(R2BF가 '잊힘'을 거부한 경우, **거부된 '잊힘' 작업이 여기에 다시 표시**됩니다. 확인 후 다시 수행하세요.)")

    pending_forget_certs = {k: v for k, v in st.session_state.certificate_db.items() if
                            v["current_status"] == "Pending_Forget"}
    if not pending_forget_certs:
        st.info("현재 대기 중인 '잊힘' 작업이 없습니다.")
    else:
        for cert_id, cert in pending_forget_certs.items():
            with st.expander(
                    f"**{cert_id} (잊힘 대기)** | 모델: {cert['content']['model_name']} | 요청자: {cert['requester_id']}"):

                last_log_message = cert['log'][-1]['message']
                if "거부" in last_log_message and cert['log'][-1]['actor'] == "R2BF 부서":
                    try:
                        reason_text = last_log_message.split('(사유: ')[1].split(')')[0]
                    except IndexError:
                        reason_text = "N/A"
                    st.error(f"R2BF 부서가 이 '잊힘' 작업을 거부했습니다. (사유: {reason_text})\n\n'잊힘' 알고리즘을 다시 수행하여 R2BF에 승인을 요청하세요.")

                st.write("**삭제 요청 데이터셋:**")
                st.markdown(f"> {cert['content']['deleted_data']}")
                st.button(
                    "▶️ '잊힘' 알고리즘 수행 (→ R2BF 승인 요청)",
                    key=f"run_forget_{cert_id}",
                    on_click=run_forgetting_callback,
                    args=(cert_id,),
                    use_container_width=True,
                    type="primary"
                )

    st.divider()

    st.subheader("장면 4: '대체' 작업 및 검토 큐")
    st.markdown(
        "R2BF의 '대체' 작업을 수행(AI 제안 생성)하고, 생성된 '대체(안)'을 검토/수정하여 R2BF에 전송합니다.\n\n(R2BF가 '대체'를 거부한 경우, **거부된 '대체(안)'이 여기에 다시 표시**됩니다. 'AI 재탐색'을 눌러주세요.)")

    combined_substitute_certs = {k: v for k, v in st.session_state.certificate_db.items() if
                                 v["current_status"] in ["Pending_Substitute", "Pending_Substitute_Review_MLOps"]}

    if not combined_substitute_certs:
        st.info("현재 대기 중인 '대체' 작업이 없습니다.")
    else:
        sorted_combined_certs = sorted(combined_substitute_certs.items(),
                                       key=lambda item: item[1]['log'][0]['timestamp'], reverse=True)

        for cert_id, cert in sorted_combined_certs:
            status = cert["current_status"]

            if status == "Pending_Substitute":
                # [상태 1: 대체 작업 대기]
                with st.expander(
                        f"**{cert_id} (대체 작업 대기)** | 모델: {cert['content']['model_name']} | 요청자: {cert['requester_id']}"):
                    st.write(f"**R2BF '잊힘' 승인 완료.**")
                    st.write("**삭제된 데이터:**")
                    st.markdown(f"> {cert['content']['deleted_data']}")

                    last_log_message = cert['log'][-1]['message']
                    if "거부" in last_log_message and cert['log'][-1]['actor'] == "R2BF 부서":
                        try:
                            reason_text = last_log_message.split('(사유: ')[1].split(')')[0]
                        except IndexError:
                            reason_text = "N/A"
                        st.error(f"R2BF 부서가 이전 '대체(안)'을 거부했습니다. (사유: {reason_text})\n\n'대체' AI 제안 생성을 다시 수행하세요.")

                    st.button(
                        "▶️ '대체' AI 제안 생성 (→ MLOps 검토)",
                        key=f"run_sub_{cert_id}",
                        on_click=run_substitute_callback,
                        args=(cert_id,),
                        use_container_width=True,
                        type="primary",
                        disabled=not st.session_state.api_model
                    )

            elif status == "Pending_Substitute_Review_MLOps":
                # [상태 2: MLOps 검토 대기]
                with st.expander(f"**{cert_id} (MLOps 검토 대기)** | 모델: {cert['content']['model_name']}"):

                    last_log_message = cert['log'][-1]['message']
                    if "거부" in last_log_message and cert['log'][-1]['actor'] == "R2BF 부서":
                        try:
                            reason_text = last_log_message.split('(사유: ')[1].split(')')[0]
                        except IndexError:
                            reason_text = "N/A"
                        st.error(
                            f"R2BF 부서가 이 '대체(안)'을 거부했습니다. (사유: {reason_text})\n\n'AI 재탐색'을 수행하거나, 내용을 수정하여 다시 요청하세요.")

                    st.warning("**[AI가 제안한 '대체' 문장]**")

                    st.text_area(
                        "AI 제안 (수정 가능):",
                        key=f"mlops_edit_{cert_id}",
                        height=500
                    )

                    col1, col2 = st.columns(2)
                    with col1:
                        st.button(
                            "🔄 AI 재탐색",
                            key=f"regen_mlops_{cert_id}",
                            on_click=regenerate_ai_suggestion_mlops_callback,
                            args=(cert_id,),
                            use_container_width=True,
                            disabled=not st.session_state.api_model
                        )
                    with col2:
                        st.button(
                            "👍 R2BF에 '대체' 승인 요청",
                            key=f"send_to_r2bf_{cert_id}",
                            on_click=send_substitute_to_r2bf_callback,
                            args=(cert_id,),
                            use_container_width=True,
                            type="primary"
                        )

# --- [장면 3 & 5] R2BF 부서 (승인팀) 대시보드 ---
with tab3:
    st.header("🛡️ R2BF 부서 (승인팀) 대시보드")

    st.subheader("장면 3: '잊힘' 승인 큐")
    st.markdown("MLOps팀이 '잊힘' 처리를 완료한 건입니다. 내용을 검토하고 '승인' 또는 '거부'합니다.")

    pending_forget_approval_certs = {k: v for k, v in st.session_state.certificate_db.items() if
                                     v["current_status"] == "Pending_Forget_Approval"}
    if not pending_forget_approval_certs:
        st.info("현재 '잊힘 승인'을 대기 중인 항목이 없습니다.")
    else:
        for cert_id, cert in pending_forget_approval_certs.items():
            with st.expander(f"**{cert_id} (잊힘 승인 대기)** | 요청자: {cert['requester_id']}"):
                st.write(f"**'잊힘' 수행자:** {cert['operator_id']}")
                st.write(f"**삭제된 데이터:** {cert['content']['deleted_data']}")
                st.info("MLOps팀의 '잊힘' 알고리즘 수행 결과를 검토(시뮬레이션)했습니다.")

                # [수정] 레이아웃 변경
                st.text_input(
                    "거부 사유 (필수)",
                    key=f"reject_reason_forget_{cert_id}",
                    placeholder="거부 사유를 MLOps에 전달합니다."
                )

                col1, col2 = st.columns(2)
                with col1:
                    st.button(
                        "👍 '잊힘' 승인 및 '대체' 작업 요청 (→ MLOps)",
                        key=f"approve_forget_{cert_id}",
                        on_click=approve_forget_callback,
                        args=(cert_id,),
                        use_container_width=True,
                        type="primary"
                    )
                with col2:
                    st.button(
                        "👎 '잊힘' 거부 (→ MLOps 재작업)",
                        key=f"reject_forget_{cert_id}",
                        on_click=reject_forget_callback,
                        args=(cert_id,),
                        use_container_width=True
                    )

    st.divider()

    st.subheader("장면 5: '대체' (최종) 승인 큐")
    st.markdown("MLOps팀이 '대체' 처리를 완료한 건입니다. MLOps가 검토/수정한 '대체' 안을 검토하고 '승인' 또는 '거부'합니다.")

    pending_substitute_approval_certs = {k: v for k, v in st.session_state.certificate_db.items() if
                                         v["current_status"] == "Pending_Substitute_Approval"}
    if not pending_substitute_approval_certs:
        st.info("현재 '대체 (최종) 승인'을 대기 중인 항목이 없습니다.")
    else:
        for cert_id, cert in pending_substitute_approval_certs.items():
            with st.expander(f"**{cert_id} (대체 승인 대기)** | 요청자: {cert['requester_id']}"):
                st.write(f"**'대체' 수행자:** {cert['operator_id']}")

                st.warning("**[MLOps가 제출한 '대체' 문장]**")
                ai_suggestion = cert['internal_ai_suggestion']
                st.markdown(f"_{ai_suggestion}_")

                st.caption("[장면 5] MLOps가 제출한 안을 검토 후 '승인' 또는 '거부'하세요.")

                # [수정] 레이아웃 변경
                st.text_input(
                    "거부 사유 (필수)",
                    key=f"reject_reason_sub_{cert_id}",
                    placeholder="거부 사유를 MLOps에 전달합니다."
                )

                col1, col2 = st.columns(2)
                with col1:
                    st.button(
                        "✅ '대체' 및 최종 승인 (인증서 발행)",
                        key=f"approve_sub_{cert_id}",
                        on_click=approve_substitute_callback,
                        args=(cert_id,),
                        use_container_width=True,
                        type="primary"
                    )
                with col2:
                    st.button(
                        "👎 '대체' 거부 (→ MLOps 재검토)",
                        key=f"reject_sub_{cert_id}",
                        on_click=reject_substitute_callback,
                        args=(cert_id,),
                        use_container_width=True
                    )

# --- 🗂️ 인증서 조회 탭 ---
with tab4:
    st.header("🗂️ 인증서 조회 (전체)")
    st.markdown("모든 R2BF 인증서의 현재 상태와 최종 결과를 조회합니다.")

    search_term = st.text_input("인증서 검색 (ID, 요청자, 내용 등으로 검색)", key="search_input").lower()

    all_certs = st.session_state.certificate_db.values()
    filtered_certs = []
    if search_term:
        for cert in all_certs:
            if (search_term in cert["cert_id"].lower() or
                    search_term in cert["requester_id"].lower() or
                    (cert["operator_id"] and search_term in cert["operator_id"].lower()) or
                    (cert["approver_id"] and search_term in cert["approver_id"].lower()) or
                    search_term in cert["content"]["deleted_data"].lower()):
                filtered_certs.append(cert)
    else:
        filtered_certs = list(all_certs)

    sorted_certs = sorted(filtered_certs, key=lambda x: x['log'][0]['timestamp'], reverse=True)

    if not sorted_certs:
        st.info(f"'{search_term}'에 해당하는 인증서가 없습니다.")

    for cert in sorted_certs:
        status = cert["current_status"]
        if status == "Completed":
            color = "success"
            status_text = "처리 완료"
        elif "Pending" in status:
            color = "warning"
            status_text = "승인 대기 중"
        else:
            color = "info"
            status_text = "처리 중"

        with st.expander(f"**{cert['cert_id']}** | 상태: **{status_text}** | 요청자: {cert['requester_id']}"):
            st.markdown(f"**1. 인증서 고유 번호:** `{cert['cert_id']}`")
            st.markdown(f"**2. 요청자:** `{cert['requester_id']}`")
            st.markdown(f"**3. 처리자 (MLOps):** `{cert['operator_id'] if cert['operator_id'] else 'N/A'}`")
            st.markdown(f"**4. 최종 승인자 (R2BF):** `{cert['approver_id'] if cert['approver_id'] else 'N/A'}`")
            st.markdown(f"**5. 처리 완료일:** `{cert['completion_date'] if cert['completion_date'] else 'N/A'}`")

            st.markdown("---")
            st.markdown("#### 처리 내용")

            # [수정] '대상 모델' 추가
            st.markdown(f"**대상 모델:** {cert['content']['model_name']}")

            if cert['current_status'] in ["Pending_Forget", "Pending_Forget_Approval", "Forgetting_In_Progress"]:
                st.caption("삭제 요청 데이터:")
            else:
                st.caption("삭제된 데이터:")

            st.markdown(f"> {cert['content']['deleted_data']}")

            st.caption("적용된 대체 정보 (최종 승인 시 표시):")

            replacement_text = cert['content']['replacement_data']

            if not replacement_text:
                replacement_text = '(아직 "대체"가 완료되지 않았습니다.)'

            st.markdown(f"{replacement_text}")

            st.markdown("---")
            st.markdown("#### 6. 처리 로그 (Log)")
            log_data = [{"Timestamp": log["timestamp"], "Status": log["status"], "Actor": log["actor"],
                         "Message": log["message"]} for log in cert["log"]]
            st.dataframe(log_data, use_container_width=True)