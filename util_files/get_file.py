import requests

submission_rplfile_id = 8


def getCompressedFile():
    print(f"Obteniendo submission files {submission_rplfile_id}....")
    # GET SUBMISSION FILES
    submission_rplfile_response = requests.get(f"{producer_base_api}/api/v3/RPLFiles/{submission_rplfile_id}")

    if submission_rplfile_response.status_code != 200:
        raise Exception("Error al obtener el comprimido de submission")

    with open('./submission_rplfiles.tar.gz', 'wb') as sf:
        sf.write(submission_rplfile_response.content)


def getExtractedFile():
    print(f"Obteniendo submission files {submission_rplfile_id}....")
    # GET SUBMISSION FILES
    submission_rplfile_response = requests.get(f"{producer_base_api}/api/v3/extractedRPLFile/{submission_rplfile_id}")

    if submission_rplfile_response.status_code != 200:
        raise Exception("noooo")

    print(submission_rplfile_response.content)

getExtractedFile()