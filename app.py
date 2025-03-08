import streamlit as st
import autopep8
import requests

st.set_page_config(
    layout="wide",
    page_title="Multi-Language Code Formatter",
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


# -------------------- Utility Functions -------------------- #

def preprocess_code_python(raw_code: str) -> str:
    """
    For Python code only:
    - Convert uppercase 'If', 'Else:' etc. to lowercase 'if', 'else:' to fix
      partial syntax problems.
    """
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


def fix_block_indentation_python(raw_code: str, indent_size: int = 4) -> str:
    """
    A simplified approach to fix indentation for Python block structures.
    This is not a perfect solution but helps in some basic cases.
    """
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
                    # Skip blank lines
                    if not next_stripped:
                        j += 1
                        continue
                    # If next line is not more-indented, fix it
                    if next_indent <= indent_level:
                        needed_indent = indent_level + indent_size
                        new_line = " " * needed_indent + next_stripped
                        processed_lines[j] = [new_line, needed_indent]
                    break
        i += 1
    return "\n".join(item[0] for item in processed_lines)


def format_python_code(raw_code: str, block_fix_passes: int) -> str:
    """
    Full pipeline for Python code formatting:
      1) Preprocess uppercase keywords
      2) Attempt repeated block indentation fixes
      3) Use autopep8 for final pass(es)
    """
    # Step 1: Preprocess
    code_step1 = preprocess_code_python(raw_code)

    # Step 2: Indentation fixes
    code_step2 = code_step1
    for _ in range(block_fix_passes):
        code_step2 = fix_block_indentation_python(code_step2, indent_size=4)

    # Step 3: autopep8 (two passes)
    try:
        pass1 = autopep8.fix_code(
            code_step2,
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
        return pass2
    except Exception as e:
        # If autopep8 fails (e.g., syntax error), return partial result
        return code_step2


def minimal_cleanup_for_non_python(raw_code: str) -> str:
    """
    A minimal cleanup approach:
      - Strip trailing spaces
      - Remove excessive empty lines
    """
    lines = raw_code.split("\n")
    lines = [line.rstrip() for line in lines]
    cleaned_lines = []
    last_line_blank = False
    for line in lines:
        if line.strip() == "":
            if last_line_blank:
                continue
            last_line_blank = True
        else:
            last_line_blank = False
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines)


def format_sas_code(raw_code: str) -> str:
    """
    A basic formatter for SAS code:
      - Cleans up extra spaces and empty lines.
      - Applies simple block indentation based on common SAS keywords.
    """
    cleaned = minimal_cleanup_for_non_python(raw_code)
    lines = cleaned.split("\n")
    formatted_lines = []
    indent_level = 0

    # Keywords to start a block and to end a block in SAS
    sas_block_start = ("proc ", "data ")
    sas_block_end = ("run;", "quit;")

    for line in lines:
        stripped = line.strip()
        lower_stripped = stripped.lower()
        # Check if the line signals the end of a block
        if any(lower_stripped.startswith(kw) for kw in sas_block_end):
            indent_level = max(indent_level - 1, 0)
            formatted_lines.append("    " * indent_level + stripped)
        else:
            formatted_lines.append("    " * indent_level + stripped)
            if any(lower_stripped.startswith(kw) for kw in sas_block_start):
                indent_level += 1

    return "\n".join(formatted_lines)


def format_vba_code(raw_code: str) -> str:
    """
    A basic formatter for VBA code:
      - Cleans up extra spaces and empty lines.
      - Applies simple block indentation based on common VBA block keywords.
    """
    cleaned = minimal_cleanup_for_non_python(raw_code)
    lines = cleaned.split("\n")
    formatted_lines = []
    indent_level = 0

    # Define VBA block starting and ending keywords
    vba_block_start = ("sub ", "function ", "if ", "for ", "while ", "select case", "with")
    vba_block_end = ("end sub", "end function", "end if", "next", "wend", "end select", "end with")

    for line in lines:
        stripped = line.strip()
        lower_stripped = stripped.lower()
        # Check if the line is a block-ending keyword
        if any(lower_stripped.startswith(kw) for kw in vba_block_end):
            indent_level = max(indent_level - 1, 0)
            formatted_lines.append("    " * indent_level + stripped)
        # Special handling for Else to align with If
        elif lower_stripped == "else" or lower_stripped.startswith("else "):
            indent_level = max(indent_level - 1, 0)
            formatted_lines.append("    " * indent_level + stripped)
            indent_level += 1
        else:
            formatted_lines.append("    " * indent_level + stripped)
            if any(lower_stripped.startswith(kw) for kw in vba_block_start):
                indent_level += 1

    return "\n".join(formatted_lines)


# --------------------- Main App Function --------------------- #
def main():
    st.markdown('<div class="outer-page-container">', unsafe_allow_html=True)
    st.title("Multi-Language Code Formatter Pro")
    st.markdown(
        """
        **Format, fix, and optimize your code effortlessly**.  
        Upload, paste, or provide a URL to your code, and let the tool handle the rest.
        """
    )

    # Initialize session variables if not already set
    if "input_code" not in st.session_state:
        st.session_state["input_code"] = ""
    if "formatted_code" not in st.session_state:
        st.session_state["formatted_code"] = ""

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

        if st.button("🗑️ Clear Input"):
            st.session_state["input_code"] = ""

        code_input_temp = st.session_state["input_code"]

        if input_mode == "📋 Paste Code":
            code_input_temp = st.text_area(
                "Paste your code below:",
                value=code_input_temp,
                height=300
            )
        elif input_mode == "📁 Upload File":
            uploaded_file = st.file_uploader("Upload a source file", type=["py", "txt", "sas", "bas"])
            if uploaded_file is not None:
                code_input_temp = uploaded_file.read().decode("utf-8")
        else:  # "🌐 Fetch from URL"
            code_url = st.text_input("Enter the URL of your code file:")
            if code_url:
                try:
                    response = requests.get(code_url)
                    if response.status_code == 200:
                        code_input_temp = response.text
                    else:
                        st.warning(f"Failed to fetch file. Status code: {response.status_code}")
                except Exception as e:
                    st.error(f"Error fetching file: {e}")

        st.session_state["input_code"] = code_input_temp

    # =============== Section 2: Configuration =============== #
    with col_settings:
        st.subheader("⚙️ Configuration")

        selected_language = st.selectbox(
            "Select Programming Language",
            ["Python", "SAS", "VBA"],
            index=0
        )

        block_fix_passes = 0
        if selected_language == "Python":
            block_fix_passes = st.slider(
                "Block Indentation Fix Passes (Python only)",
                min_value=0,
                max_value=3,
                value=1
            )

        if st.button("✨ Format & Refine Code"):
            raw_code = st.session_state["input_code"].strip()
            if raw_code:
                if selected_language == "Python":
                    formatted = format_python_code(raw_code, block_fix_passes)
                    st.session_state["formatted_code"] = formatted
                elif selected_language == "SAS":
                    formatted = format_sas_code(raw_code)
                    st.session_state["formatted_code"] = formatted
                elif selected_language == "VBA":
                    formatted = format_vba_code(raw_code)
                    st.session_state["formatted_code"] = formatted
                else:
                    st.warning("Unsupported language selected.")
            else:
                st.warning("No code to format. Please paste or upload code.")

    # =============== Section 3: Output & Download =============== #
    with col_output:
        st.subheader("📄 Output & Download")

        # Place Clear Output and Download buttons right under the header
        col_buttons = st.columns(2)
        with col_buttons[0]:
            if st.button("🗑️ Clear Output"):
                st.session_state["formatted_code"] = ""
        with col_buttons[1]:
            st.download_button(
                label="📥 Download Refined Code",
                data=st.session_state["formatted_code"],
                file_name="formatted_code.txt",
                mime="text/plain",
                disabled=(not st.session_state["formatted_code"].strip())
            )

        # Apply syntax highlighting based on selected language
        lang_map = {
            "Python": "python",
            "SAS": "sas",
            "VBA": "vba"
        }
        highlight_language = lang_map.get(selected_language, "text")
        st.code(st.session_state["formatted_code"], language=highlight_language, line_numbers=True)

    st.markdown('<hr class="bottom-line" />', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
