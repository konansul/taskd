import streamlit as st
import requests
import tempfile
import os

BACKEND_URL = "https://taskd-backend-production.up.railway.app"

def main():
    st.title("Sənəddən Təqdimat Yaratma")

    uploaded_file = st.file_uploader("PDF və ya DOCX faylını yükləyin", type=["pdf", "docx"])
    slide_count = st.number_input("Slaydların sayı", min_value=5, value=6)
    include_visuals = st.radio("Vizual əlavə olunsun?", ("Bəli", "Xeyr"), index=1)

    if uploaded_file and st.button("PPTX Yarat"):
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        with open(tmp_path, "rb") as f:
            files = {"file": (uploaded_file.name, f, "application/octet-stream")}
            data = {
                "slide_count": slide_count,
                "include_visuals": include_visuals == "Bəli",
                "store": True
            }

            with st.spinner("Təqdimat yaradılır..."):
                resp = requests.post(f"{BACKEND_URL}/generate", files=files, data=data)

        os.unlink(tmp_path)

        if resp.status_code != 200:
            st.error(f"Xəta: {resp.text}")
            return

        result = resp.json()
        st.success("Təqdimat uğurla yaradıldı!")
        st.json(result)

        # Download link
        presentation_id = result.get("presentation_id")
        if presentation_id:
            pptx_url = f"{BACKEND_URL}/presentations/{presentation_id}/export/pptx"
            st.markdown(f"[📥 PPTX faylını yüklə]({pptx_url})")

if __name__ == "__main__":
    main()