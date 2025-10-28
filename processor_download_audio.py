from __future__ import annotations

from pathlib import Path

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from processor import Processor

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class ProcessorDownloadAudio(Processor):
    def get_name(self) -> str:
        return "download audio"

    def get_input_folder_name(self) -> str:
        return "resource"

    def get_output_folder_name(self) -> str:
        return "audio"

    def get_file_extension(self) -> str:
        return ".mp3"
    
    def get_input_folder_name(self):
        return "/"


    def process(
        self,
        input_folder: str,
        item_name: str,
        output_folder: str,
        file_name: str | None = None,
        sermon = None,
    ) -> bool:
        resource_link: str = sermon.get('source')        
        if not resource_link:
            return False


        destination_dir = Path(output_folder)
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination_path = destination_dir / f"{item_name}.mp3"

        try:
            with requests.get(resource_link, stream=True, timeout=30, verify=False) as response:
                response.raise_for_status()

                with destination_path.open("wb") as target_file:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            target_file.write(chunk)
        except requests.RequestException as exc:
            raise RuntimeError(f"Failed to download audio from {resource_link}") from exc
        except Exception:
            if destination_path.exists():
                destination_path.unlink()
            raise

        return True

if __name__ == "__main__":
    processor = ProcessorDownloadAudio()
    print(processor.get_input_folder_name())
