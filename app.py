import streamlit as st
import base64 
import time
import pandas as pd
from io import StringIO, BytesIO
import zipfile
import os
from PIL import Image
import json

# Check for required dependencies
try:
    import xlsxwriter
    XLSXWRITER_AVAILABLE = True
except ImportError:
    XLSXWRITER_AVAILABLE = False

try:
    import openpyxl
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

# Utils
timestr = time.strftime("%Y%m%d-%H%M%S")

# Dependency check function
def check_dependencies():
    missing = []
    requirements = {
        'xlsxwriter': 'Excel export (recommended)',
        'openpyxl': 'Excel export (alternative)',
        'Pillow': 'Image processing'
    }
    
    for package, purpose in requirements.items():
        try:
            __import__(package)
        except ImportError:
            missing.append((package, purpose))
    return missing

# Enhanced File Download Functions
def text_downloader(raw_text, filename_prefix="text_file"):
    """Enhanced text downloader with more options"""
    b64 = base64.b64encode(raw_text.encode()).decode()
    new_filename = f"{filename_prefix}_{timestr}.txt"
    
    st.markdown("### Download Options")
    col1, col2 = st.columns(2)
    
    with col1:
        st.download_button(
            label="Download as TXT",
            data=raw_text,
            file_name=new_filename,
            mime="text/plain"
        )
    
    with col2:
        st.markdown("#### Alternative Download")
        href = f'<a href="data:file/txt;base64,{b64}" download="{new_filename}">Right-click and save link as</a>'
        st.markdown(href, unsafe_allow_html=True)

def csv_downloader(data, filename_prefix="data"):
    """Enhanced CSV downloader with format options"""
    st.markdown("### CSV Download Options")
    
    # CSV configuration options
    col1, col2 = st.columns(2)
    with col1:
        delimiter = st.selectbox("Delimiter", [",", ";", "\t", "|"], index=0)
    with col2:
        encoding = st.selectbox("Encoding", ["utf-8", "ascii", "iso-8859-1"], index=0)
    
    csv = data.to_csv(index=False, sep=delimiter)
    new_filename = f"{filename_prefix}_{timestr}.csv"
    
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name=new_filename,
        mime="text/csv",
        help=f"CSV file with {delimiter} delimiter"
    )

def excel_downloader(data, filename_prefix="data"):
    """Download as Excel file with fallback engines"""
    output = BytesIO()
    
    # Try available engines in order of preference
    engines = []
    if XLSXWRITER_AVAILABLE:
        engines.append('xlsxwriter')
    if OPENPYXL_AVAILABLE:
        engines.append('openpyxl')
    
    if not engines:
        st.warning("""
        Excel export requires either xlsxwriter or openpyxl package. 
        Install with: 
        ```bash
        pip install xlsxwriter openpyxl
        ```
        """)
        return
    
    for engine in engines:
        try:
            with pd.ExcelWriter(output, engine=engine) as writer:
                data.to_excel(writer, index=False, sheet_name='Sheet1')
            excel_data = output.getvalue()
            
            new_filename = f"{filename_prefix}_{timestr}.xlsx"
            
            st.download_button(
                label="Download Excel",
                data=excel_data,
                file_name=new_filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            return
        except Exception as e:
            continue
    
    st.error("Failed to create Excel file with all available engines")

def create_zip(files):
    """Create a zip file from multiple files"""
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for file_name, file_content in files.items():
            zip_file.writestr(file_name, file_content)
    return zip_buffer.getvalue()

# Enhanced FileDownloader Class
class FileDownloader:
    """Enhanced file downloader with multiple format support"""
    def __init__(self, data, filename='file', file_ext='txt', **kwargs):
        self.data = data
        self.filename = filename
        self.file_ext = file_ext.lower()
        self.kwargs = kwargs
        
    def _get_mime_type(self):
        mime_types = {
            'txt': 'text/plain',
            'csv': 'text/csv',
            'json': 'application/json',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'zip': 'application/zip'
        }
        return mime_types.get(self.file_ext, 'application/octet-stream')
    
    def download(self):
        new_filename = f"{self.filename}_{timestr}.{self.file_ext}"
        
        if isinstance(self.data, pd.DataFrame):
            if self.file_ext == 'csv':
                data = self.data.to_csv(**self.kwargs)
            elif self.file_ext == 'xlsx':
                excel_downloader(self.data, filename_prefix=self.filename)
                return
            else:
                data = self.data.to_string()
        elif self.file_ext in ['png', 'jpg'] and PILLOW_AVAILABLE:
            data = self.data
        else:
            data = str(self.data).encode()
        
        st.download_button(
            label=f"Download as {self.file_ext.upper()}",
            data=data,
            file_name=new_filename,
            mime=self._get_mime_type(),
            help=f"Download file as {self.file_ext.upper()} format"
        )

# Main App
def main():
    st.set_page_config(
        page_title="Advanced File Downloader",
        page_icon="📁",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Check dependencies
    missing_deps = check_dependencies()
    if missing_deps:
        with st.sidebar.expander("⚠️ Missing Dependencies", expanded=True):
            st.warning("Some features require additional packages:")
            for package, purpose in missing_deps:
                st.code(f"pip install {package}  # {purpose}", language="bash")
    
    st.title("📁 Advanced File Downloader")
    st.markdown("""
    Upload, process, and download files in various formats with additional options.
    """)
    
    menu = ["Text Downloader", "CSV/Excel Tools", "Image Tools", "Multi-File Export", "About"]
    choice = st.sidebar.selectbox("Menu", menu)
    
    if choice == "Text Downloader":
        st.header("Text File Generator")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Input Text")
            default_text = """This is a sample text. Replace with your own content.
You can type multiple lines here.
The text will be saved exactly as formatted."""
            my_text = st.text_area("Your Message", value=default_text, height=200)
            
        with col2:
            st.subheader("Download Options")
            filename = st.text_input("Filename prefix", value="document")
            if st.button("Generate Download Link"):
                text_downloader(my_text, filename_prefix=filename)
                
                # Additional format options
                st.markdown("### Alternative Formats")
                downloader = FileDownloader(my_text, filename=filename, file_ext='txt')
                downloader.download()
                
                downloader = FileDownloader(my_text, filename=filename, file_ext='json')
                downloader.download()
    
    elif choice == "CSV/Excel Tools":
        st.header("CSV & Excel Tools")
        
        uploaded_file = st.file_uploader("Upload CSV or Excel file", type=['csv', 'xlsx'])
        
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                
                st.success("File successfully loaded!")
                st.dataframe(df.head())
                
                st.subheader("Data Summary")
                st.write(df.describe())
                
                st.subheader("Download Options")
                filename = st.text_input("Filename prefix", value="data_export")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("### CSV Options")
                    csv_downloader(df, filename_prefix=filename)
                
                with col2:
                    st.markdown("### Excel Options")
                    excel_downloader(df, filename_prefix=filename)
                
                # Advanced options
                st.markdown("### Advanced Export")
                selected_columns = st.multiselect("Select columns to export", df.columns.tolist(), default=df.columns.tolist())
                if selected_columns:
                    filtered_df = df[selected_columns]
                    FileDownloader(filtered_df, filename=f"{filename}_filtered", file_ext='csv').download()
                    FileDownloader(filtered_df, filename=f"{filename}_filtered", file_ext='xlsx').download()
            
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")
    
    elif choice == "Image Tools":
        st.header("Image Tools")
        
        if not PILLOW_AVAILABLE:
            st.warning("Image processing requires Pillow package. Install with: pip install Pillow")
        else:
            uploaded_image = st.file_uploader("Upload an image", type=['png', 'jpg', 'jpeg'])
            
            if uploaded_image is not None:
                image = Image.open(uploaded_image)
                st.image(image, caption="Uploaded Image", use_column_width=True)
                
                st.subheader("Image Download Options")
                filename = st.text_input("Filename prefix", value="image")
                
                # Convert to different formats
                img_buffer = BytesIO()
                image.save(img_buffer, format='PNG')
                
                FileDownloader(img_buffer.getvalue(), filename=filename, file_ext='png').download()
                FileDownloader(img_buffer.getvalue(), filename=filename, file_ext='jpg').download()
    
    elif choice == "Multi-File Export":
        st.header("Export Multiple Files")
        
        st.info("Create a zip file containing multiple formats of your data")
        
        data_input = st.text_area("Enter data to export in multiple formats", height=150)
        
        if data_input:
            # Create files for zip
            files_to_zip = {
                "data.txt": data_input,
                "data.csv": pd.DataFrame([line.split() for line in data_input.split('\n')]).to_csv(index=False),
                "data.json": json.dumps({"content": data_input.split('\n')}, indent=2)
            }
            
            zip_data = create_zip(files_to_zip)
            
            st.download_button(
                label="Download as ZIP",
                data=zip_data,
                file_name=f"multi_export_{timestr}.zip",
                mime="application/zip"
            )
    
    else:
        st.header("About")
        st.markdown("""
        ### Advanced File Downloader App
        
        **Features:**
        - Download text files with custom names
        - CSV/Excel conversion and export with configurable options
        - Image format conversion
        - Multi-file zip exports
        - Advanced download options for each format
        
        **Tech Stack:**
        - Python
        - Streamlit
        - Pandas
        - Pillow (for image processing)
        
        *Created with ❤️ for easy file conversions*
        """)

if __name__ == '__main__':
    main()