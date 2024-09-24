"""
Given a list of repositories, this script will attempt to match them with the Vendor and Product names from CVE JSONs.
"""

# Assume this repo:
# is at ../cvelist
import pathlib
import os
import re
import orjson
from tqdm import tqdm

# Input files/folders
cvelist = os.path.join(os.path.dirname(__file__), '../cves')
repolist = os.path.join(os.path.dirname(__file__), 'repos.txt')
id_to_name = os.path.join(os.path.dirname(__file__), 'cve-id-to-name.json')

# Output files
output_file = os.path.join(os.path.dirname(__file__), 'output/repos_to_nvd.csv')
missing_file = os.path.join(os.path.dirname(__file__), 'output/missing_repos.txt')
fix_file = os.path.join(os.path.dirname(__file__), 'output/manual_fix_repos.txt')

URL_REGEX = re.compile(r"https?://(?:www\.)?[-a-zA-Z0-9@:%._+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_+.~#?&/=]*)")

class Repo:
	ids: tuple
	def __init__(self, name=None, vendor=None, url=None):
		self.ids = (str(name).lower(), str(vendor).lower())
		self.url = url
		self.matches = list()
		self.cve_vendor = list()
		self.cve_product = list()

	def match_with(self, vendors, products, urls):
		for i in range(len(vendors)):
			v = str(vendors[i])
			p = str(products[i])
			if v.lower() in self.ids and p.lower() in self.ids:
				return self.add_match([v], [p], [])

		url_matches = []
		for url in urls:
			if f"https://github.com/{self.url}".lower() in url.lower():
				url_matches.append(url)


		if url_matches and len(url_matches) > 0:
			self.add_match(vendors, products, url_matches)

	def add_match(self, vendor, product, urls):
		for u in urls:
			self.matches.append(u)
		for p in product:
			self.cve_product.append(p)
		for v in vendor:
			self.cve_vendor.append(v)


	def resolve(self):
		for i in range(len(self.cve_vendor)):
			if i >= len(self.cve_vendor):
				break
			ven = str(self.cve_vendor[i])
			prod = str(self.cve_product[i])
			if ven.lower() == self.ids[1] and prod.lower() == self.ids[0]:
				self.cve_vendor = [ven]
				self.cve_product = [prod]

		for i in range(len(self.cve_product)):
			if i >= len(self.cve_product):
				break
			prod = self.cve_product[i]
			ven = self.cve_vendor[i]
			if str(self.url).lower() == str(prod).lower():
				self.cve_vendor = [ven]
				self.cve_product = [prod]

	def __str__(self):
		out = f"[ {self.url} ]\n"
		out += f"Vendor: {set(self.cve_vendor)}\nProduct: {set(self.cve_product)}\n"
		return out + "-"*80


	def __repr__(self):
		return self.__str__()

def read_data():
	id_map = dict()
	repos: list[Repo] = list()
	with open(repolist, 'r') as f:
		for repo in f:
			repo = repo.strip()
			vendor, name = repo.strip().split('/')
			repos.append(Repo(name, vendor, repo))

	with open(id_to_name, 'r') as f:
		id_map = orjson.loads(f.read())

	return repos, id_map

def parse_jsons(repos):
	cvelist_path = pathlib.Path(cvelist)
	for p in tqdm(list(cvelist_path.rglob("CVE*.json")), desc="Parsing JSONs"):
		with open(p, 'r') as f:
			try:
				data_str = f.read()
				data = orjson.loads(data_str)

				affected = data.get("containers", {}).get("cna", {}).get("affected", [])
				products = list([
					a.get("product") for a in affected
				])
				vendors = list([
					a.get("vendor") for a in affected
				])
				urls = re.findall(URL_REGEX, data_str)

				for repo in repos:
					repo.match_with(vendors, products, urls)

			except UnicodeDecodeError as e:
				print(e.reason)
				print(f"ERROR loading {p}")

def generate_outputs(repos: list[Repo]):
	output_missing = ""
	output_fix = ""
	output = "github repo,cve vendor,cve product\n"

	for repo in tqdm(repos, desc="Writing outputs"):
		repo.resolve()
		ven_len = len(repo.cve_vendor)
		prod_len = len(repo.cve_product)
		if ven_len + prod_len == 0:
			output_missing += f"{repo.url}\n"
		elif ven_len > 1 or prod_len > 1 or ven_len + prod_len == 1:
			output_fix += f"{repo}\n"
		else:
			ven = repo.cve_vendor.pop() if ven_len > 0 else None
			prod = repo.cve_product.pop() if prod_len > 0 else None
			if ven and prod and ven != "n/a" and prod != "n/a":
				output += f"{repo.url},{ven},{prod}\n"
			else:
				output_fix += f"{repo}\n"

	return output, output_missing, output_fix

def write_output(output, output_missing, output_fix):
	with open(output_file, 'w') as f:
		f.write(output)

	with open(missing_file, 'w') as f:
		f.write(output_missing)

	with open(fix_file, 'w') as f:
		f.write(output_fix)

def main():
	repos, id_map = read_data()
	parse_jsons(repos)
	output, output_missing, output_fix = generate_outputs(repos)
	write_output(output, output_missing, output_fix)

if __name__ == "__main__":
	main()
