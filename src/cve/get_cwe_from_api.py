import requests
import os
import json
from pathlib import Path

NVD_API = 'https://services.nvd.nist.gov/rest/json/cves/2.0'

# Input files/folder
cves_no_cwe_list = os.path.join(os.path.dirname(__file__), 'output/c_cve_no_cwe.txt')
cves_yes_cwe_list = os.path.join(os.path.dirname(__file__), 'output/c_cve_yes_cwe.txt')

def load_cves_no_cwe():
		with open(Path(cves_no_cwe_list), 'r') as f:
				cves_no = f.readlines()
		with open(Path(cves_yes_cwe_list), 'r') as f:
				cves_yes = f.readlines()
		return cves_no, cves_yes

def get_cwe_from_api(cve):
	request_url = f'{NVD_API}?cveId={cve}'
	# https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=CVE-2024-42080
	# https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=CVE-2024-42080
	response = requests.get(request_url)

	# Check if response is empty or contains an error
	if response.status_code != 200:
			print(f'Error: {response.status_code}, Content: {response.text}')
			return None

	try:
		data = response.json()
	except requests.exceptions.JSONDecodeError:
		print("Error: Response is not valid JSON")
		print(f'Response content: {response.text}')
		return None


	values = []

	for v in data.get('vulnerabilities', []):
		for w in v.get('cve', {}).get('weaknesses', []):
			for d in w.get('description', []):
				if 'value' in d:
					values.append(d['value'])

	return values

def main():
	cves_no_cwe, cves_yes_cwe = load_cves_no_cwe()
	# for cve in cves_no_cwe:
	# 	cve = cve.strip()
	# 	cwes = get_cwe_from_api(cve)
	# 	if len(cwes) == 1:
	# 		print(f'{cve}\t{cwes[0]}')
	# 	elif len(cwes) == 0:
	# 		continue
	# 	else:
	# 		print(f'{cve}\t{",".join(cwes)}')

	for cve in cves_no_cwe:
		if cve in cves_yes_cwe:
			continue
		print(cve.strip())

	pass

if __name__ == '__main__':
	main()
