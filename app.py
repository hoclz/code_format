import streamlit as st
import autopep8
import requests

st.set_page_config(
    layout="wide",
    page_title="Python Code Formatter Pro",
    page_icon=":snake:"
)

# ----- Custom CSS for layout, borders, lines, and top offset -----
st.markdown(
    """
    <style>
    /* Pull the main container further up */
    .block-container {
        padding-top: 0rem !important;
        margin-top: -2.2rem !important;
    }

    /* Outer rectangle for entire page content (no borders, no shadow) */
    .outer-page-container {
        border: none;
        border-radius: 10px;
        padding: 30px;
        margin-bottom: 20px;
        background-color: #FFFFFF;
        box-shadow: none;
    }

    /* Vertical dividers between columns */
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) {
        border-right: 2px solid #ccc;
        padding-right: 20px !important;
        margin-right: 20px !important;
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) {
        border-right: 2px solid #ccc;
        padding-right: 20px !important;
        margin-right: 20px !important;
    }

    /* Text area background color */
    div.stTextArea textarea {
        background-color: #F0F0F8;
    }

    /* A custom bottom horizontal line inside the container */
    .bottom-line {
        border: none;
        border-top: 2px solid #ccc;
        margin-top: 25px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --------------------- Utility Functions --------------------- #
def preprocess_code(raw_code: str) -> str:
    replacements = {
        "Else:": "else:",
        "Elif ": "elif ",
        "If ": "if ",
        "While ": "while ",
        "For ": "for ",
    }
    lines = raw_code.splitlines(keepends=True)
    new_lines = []
    for line in lines:
        for old, new in replacements.items():
            if old in line:
                line = line.replace(old, new)
        new_lines.append(line)
    return "".join(new_lines)

def fix_block_indentation(raw_code: str, indent_size: int = 4) -> str:
    lines = raw_code.splitlines()
    block_keywords = (
        "if ", "elif ", "else:", "for ", "while ",
        "def ", "class ", "with ", "try:", "except "
    )
    processed_lines = []
    for line in lines:
        stripped_line = line.lstrip()
        leading_spaces = len(line) - len(stripped_line)
        processed_lines.append([line, leading_spaces])

    i = 0
    while i < len(processed_lines):
        line, indent_level = processed_lines[i]
        line_stripped = line.strip()
        if line_stripped.endswith(":"):
            lower_stripped = line_stripped.lower()
            if any(lower_stripped.startswith(kw) for kw in block_keywords):
                j = i + 1
                while j < len(processed_lines):
                    next_line, next_indent = processed_lines[j]
                    next_stripped = next_line.strip()
                    if next_stripped == "":
                        j += 1
                        continue
                    if next_indent <= indent_level:
                        needed_indent = indent_level + indent_size
                        new_line = " " * needed_indent + next_stripped
                        processed_lines[j] = [new_line, needed_indent]
                    break
        i += 1
    return "\n".join(item[0] for item in processed_lines)

# --------------------- Main App Function --------------------- #
def main():
    st.markdown('<div class="outer-page-container">', unsafe_allow_html=True)
    st.title("Python Code Formatter Pro")
    st.markdown(
        """
        **Format, fix, and optimize your Python code effortlessly.**  
        Upload, paste, or provide a URL to your Python code, and let the tool handle the rest.
        """
    )

    # Ensure these session variables exist
    if "input_code" not in st.session_state:
        st.session_state["input_code"] = ""  # For user input
    if "formatted_code" not in st.session_state:
        st.session_state["formatted_code"] = ""  # For processed output

    st.markdown("---")

    col_input, col_settings, col_output = st.columns([4, 3, 5], gap="large")

    # =============== Section 1: Code Input =============== #
    with col_input:
        st.subheader("🔍 Code Input & Retrieval")

        input_mode = st.radio(
            "Select Code Source",
            ["📋 Paste Code", "📁 Upload File", "🌐 Fetch from URL"],
            horizontal=False
        )

        # If user clicks Clear Input, we just reset the 'input_code' in session
        if st.button("🗑️ Clear Input"):
            st.session_state["input_code"] = ""

        code_input_temp = st.session_state["input_code"]  # A temp local copy

        # We'll present the text area or handle file/URL below:
        if input_mode == "📋 Paste Code":
            code_input_temp = st.text_area(
                "Paste your Python code below:",
                value=code_input_temp,
                height=300
            )

        elif input_mode == "📁 Upload File":
            uploaded_file = st.file_uploader("Upload a .py file", type=["py"])
            if uploaded_file is not None:
                code_input_temp = uploaded_file.read().decode("utf-8")

        else:  # "🌐 Fetch from URL"
            code_url = st.text_input("Enter the URL of your Python file:")
            if code_url:
                try:
                    response = requests.get(code_url)
                    if response.status_code == 200:
                        code_input_temp = response.text
                    else:
                        st.warning(f"Failed to fetch file. Status code: {response.status_code}")
                except Exception as e:
                    st.error(f"Error fetching file: {e}")

        # Update session state with the final input
        st.session_state["input_code"] = code_input_temp

    # =============== Section 2: Configuration =============== #
    with col_settings:
        st.subheader("⚙️ Configuration")

        python_version = st.selectbox(
            "Select Python Version",
            ["Python 3.8", "Python 3.9", "Python 3.10"],
            index=0
        )

        block_fix_passes = st.slider(
            "Block Indentation Fix Passes",
            min_value=0,
            max_value=3,
            value=1
        )

        if st.button("✨ Format & Refine Code"):
            raw_code = st.session_state["input_code"].strip()
            if raw_code:
                # Step 1: Preprocess uppercase keywords
                step1_code = preprocess_code(raw_code)
                # Step 2: Attempt block indentation fixes
                step2_code = step1_code
                for _ in range(block_fix_passes):
                    step2_code = fix_block_indentation(step2_code, indent_size=4)
                # Step 3: Attempt autopep8 formatting
                try:
                    pass1 = autopep8.fix_code(
                        step2_code,
                        options={
                            "aggressive": 2,
                            "experimental": True,
                            "indent_size": 4
                        }
                    )
                    pass2 = autopep8.fix_code(
                        pass1,
                        options={
                            "aggressive": 2,
                            "experimental": True,
                            "indent_size": 4
                        }
                    )
                    st.session_state["formatted_code"] = pass2
                except Exception as e:
                    st.warning(
                        f"Auto-formatting failed due to syntax errors:\n{e}\n"
                        "You may need to manually fix missing blocks or invalid statements."
                    )
                    st.session_state["formatted_code"] = step2_code
            else:
                st.warning("No code to format. Please paste or upload code.")

    # =============== Section 3: Output =============== #
    with col_output:
        st.subheader("📄 Output & Download")

        st.code(st.session_state["formatted_code"], language="python", line_numbers=True)

        if st.button("🗑️ Clear Output"):
            st.session_state["formatted_code"] = ""

        st.download_button(
            label="📥 Download Refined Code",
            data=st.session_state["formatted_code"],
            file_name="formatted_code.py",
            mime="text/plain",
            disabled=(not st.session_state["formatted_code"].strip())
        )

    # A bottom horizontal line inside the container
    st.markdown('<hr class="bottom-line" />', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
