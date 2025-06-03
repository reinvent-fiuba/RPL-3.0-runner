import requests

submission_file_id = 8


def getCompressedFile():
    print(f"Obteniendo submission files {submission_file_id}....")
    # GET SUBMISSION FILES
    submission_file_response = requests.get(f"{producer_base_api}/api/v3/RPLFiles/{submission_file_id}")

    if submission_file_response.status_code != 200:
        raise Exception("Error al obtener el comprimido de submission")

    with open('./submission_files.tar.gz', 'wb') as sf:
        sf.write(submission_file_response.content)


def getExtractedFile():
    print(f"Obteniendo submission files {submission_file_id}....")
    # GET SUBMISSION FILES
    submission_file_response = requests.get(f"{producer_base_api}/api/v3/extractedRPLFile/{submission_file_id}")

    if submission_file_response.status_code != 200:
        raise Exception("noooo")

    print(submission_file_response.content)

getExtractedFile()