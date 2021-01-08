import sys, os, datetime, argparse
from bs4 import BeautifulSoup
import pandas as pd
from time import sleep
import warnings
import pickle as pkl
from errors import *
from tqdm import tqdm

# Solve conflict between raw_input and input on Python 2 and Python 3
import sys
if sys.version[0]=="3": raw_input=input

# Default Parameters
CSVPATH = '.' # Current folder
ERROR_KW=['your computer or network may be sending automated queries']
ROBOT_KW=['unusual traffic from your computer network', 'not a robot', '로봇']

def get_command_line_args():
    now = datetime.datetime.now()

    # Command line arguments
    parser = argparse.ArgumentParser(description='Arguments')
    parser.add_argument('--year', type=int, required=True, help='NeruIPS year to search.')
    parser.add_argument('--month', type=int, help='NeruIPS month. (Optinal)')
    parser.add_argument('--csvpath', type=str, help='Path to save the exported csv file. By default it is the current folder')

    # Parse and read arguments and assign them to variables if exists
    args, _ = parser.parse_known_args()

    if args.year > 2020:
        raise ValueError("Year > 2020 not supported.")
    elif args.year < 2010:
        raise ValueError("Year < 2010 not supported.")
    year = args.year

    month = None
    if args.month:
        if args.month < 1 or args.month > 12:
            raise ValueError("Month must be in range [1, ..., 12].")
            
        if year == now.year and args.month > now.month:
            raise ValueError("Month must be <= {}.".format(now.month))

        month = args.month

    csvpath = CSVPATH
    if args.csvpath:
        csvpath = args.csvpath

    return year, month, csvpath

def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")

def get_citations(content):
    out = 0
    for char in range(0,len(content)):
        if content[char:char+4] == '회 인용':
            end = char
            for init in range(end-7, end):
                if content[init-1] == '>':
                    break
            out = content[init:end]
        
        elif content[char:char+9] == 'Cited by ':
            init = char+9
            for end in range(init+1,init+6):
                if content[end] == '<':
                    break
            out = content[init:end]
    
    return int(out)

def setup_driver():
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.common.exceptions import StaleElementReferenceException
    except Exception as e:
        print(e)
        print("Please install Selenium and chrome webdriver for manual checking of captchas")

    print('Loading...')
    chrome_options = Options()
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument("window-size=1280,800")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36")

    driver = webdriver.Chrome(chrome_options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")


    return driver

def get_element(driver, xpath, attempts=5, _count=0):
    '''Safe get_element method with multiple attempts'''
    try:
        element = driver.find_element_by_xpath(xpath)
        return element
    except Exception as e:
        if _count<attempts:
            sleep(1)
            get_element(driver, xpath, attempts=attempts, _count=_count+1)
        else:
            print("Element not found")

def get_gscholar_contents(el):    
    if any(kw in el.text for kw in ROBOT_KW):
        raise RobotError()
    
    elif any(kw in el.text for kw in ERROR_KW):
        raise AQError()

    return el.get_attribute('innerHTML').encode('utf-8')

def save_checkpoint(idx, citations, etc):
    if idx != 0:
        with open('./temp/backup.pkl', 'wb') as f:
            pkl.dump([idx, citations, etc], f)
            
def main():
    GSCHOLAR_URL = "https://scholar.google.com/scholar?hl=en&as_sdt=0%2C5&q={}&num=1"
    
    # Variables
    year, month, csvpath = get_command_line_args()
    if month is None:
        print("Please provide month for \"cit/month\" information.")

    # Class instances
    now = datetime.datetime.now()
    driver = setup_driver()

    # Accumul.
    start_idx = 0
    citations = []
    etc = []

    if os.path.isfile('./temp/backup.pkl'):
        ans = query_yes_no("Restore from backup...?")
        if ans:
            print("Restoring from backup...")
            with open('./temp/backup.pkl', 'rb') as f:
                [start_idx, citations, etc] = pkl.load(f)

    print("Loading NeruIPS {} results".format(year))
    
    try:
        driver.get('https://papers.nips.cc/paper/{}'.format(year))
        el = get_element(driver, "/html/body")
        c = el.get_attribute('innerHTML').encode('utf-8')

    except Exception as e:
        print("No success. The following error was raised:")
        print(e)
        import pdb; pdb.set_trace()
        a = 1

    soup = BeautifulSoup(c, 'html.parser')

    list_papers_soup = soup.select("ul")[1].select("li")
    print("Found {:d} papers.".format(len(list_papers_soup)))

    authors = [paper_.select_one("i").text for paper_ in list_papers_soup]
    titles = [paper_.select_one("a").text for paper_ in list_papers_soup]
    links = ["https://papers.nips.cc{}".format(paper_.select_one("a").get("href")) for paper_ in list_papers_soup]

    for idx in tqdm(range(start_idx, len(authors)), total=len(authors), initial=start_idx):
        title_ = titles[idx]
        link = links[idx]
        authors_ = authors[idx]

        url = GSCHOLAR_URL.format(link.replace(':', '%3A').replace('/', '%2F'))
        driver.get(url)

        while(True):
            """
            While Loop 작동 매커니즘

            1. 첫번째 블록
            
            구글 스콜라 검색 결과를 읽어와서 다음 예외 상황에 대처
            
            Case (1) 캡차 풀기 요구 받은 경우
            유저가 직접 캡차를 풀고, 터미널에 엔터를 입력해주면 계속 진행.

            Case (2) Auto Query 감지에 걸린 경우
            이 경우는 구글 국가를 변경하는 방법 외에는 Bypass 불가능.
            .com -> .co.kr -> .co.uk -> .ca 순으로 변경.
            .ca 까지 모두 소진한 경우 프로그램 종료 (다시키면 됨).

            Case (3) 기타 알 수 없는 이유로 페이지 로딩이 안 됨
            Citation 수 0개로 처리하고, "etc" 열에 에러 로그 추가 및 다음 논문으로 넘어감.

            Case (3) 제외하고, 페이지 정상적으로 로딩되면 두번째 블록으로 진행
            
            2. 두번째 블록

            처음 로딩한 페이지는 높은 검색 정확도를 위해 공식 논문 페이지 주소 "links"를 검색한 것.
            결과가 나오지 않는 경우가 있으므로 이 경우에는 논문 제목으로 다시 검색.
            논문 제목으로 검색해도 결과가 나오지 않으면 인용수 0으로 기록.



            """

            #####################################################
            ################## 첫번째 블록 시작 #####################
            #####################################################
            try:
                # Try getting gscholar search results.
                el = get_element(driver, "/html/body")
                c = get_gscholar_contents(el)

            except RobotError:
                # You must solve captcha. Case (1)
                save_checkpoint(idx, citations, etc)
                raw_input("Solve captcha manually and press enter here to continue...")
                continue

            except AQError:
                # Replace the google url with one for other counturies. Case (2)
                save_checkpoint(idx, citations, etc)
                if '.com' in url:
                    url = url.replace('.com', '.co.kr')
                    GSCHOLAR_URL = GSCHOLAR_URL.replace('.com', '.co.kr')
                    driver.get(url)

                elif '.co.kr' in url:
                    url = url.replace('.co.kr', '.co.uk')
                    GSCHOLAR_URL = GSCHOLAR_URL.replace('.co.kr', '.co.uk')
                    driver.get(url)

                elif '.co.uk' in url:
                    url = url.replace('.co.uk', '.ca')
                    GSCHOLAR_URL = GSCHOLAR_URL.replace('.co.kr', '.ca')
                    driver.get(url)
                
                else:
                    raise GScholarError()
                    
                continue
            
            except Exception as e:
                # No result. Case (3)
                print("Error: No success.")
                print(e)
                etc.append(str(e))
                citations.append(0)
                break
    
            #####################################################
            ################## 첫번째 블록 종료 #####################
            #####################################################

            # Create parser
            soup = BeautifulSoup(c, 'html.parser')

            # Get stuff
            mydivs = soup.findAll("div", { "class" : "gs_r" })
            div = mydivs[0]
            
            #####################################################
            ################## 두번째 블록 시작 #####################
            #####################################################

            # Exception for no search results case.
            if any(kw in div.text for kw in ["정보가 없습니다", "no information is available"]):
                new_url = GSCHOLAR_URL.format("\""+title_.replace(' ', '+')+"\"")
                if url == new_url:
                    print("Error: No search result for {}".format(title_))
                    etc.append("No Search Results")
                    citations.append(0)
                    break

                else:
                    print("Warning: No search result with link for {}".format(title_))
                    print("Retrying Search with the title...")
                    url = new_url
                    driver.get(url)
                    continue

            #####################################################
            ################## 두번째 블록 종료 #####################
            #####################################################

            try:
                citations.append(get_citations(str(div.format_string)))
                etc.append("")
                break
                
            except:
                citations.append(0)
                etc.append("")
                break

        if idx == len(titles) - 1:
            save_checkpoint(idx+1, citations, etc)

        # Delay
        sleep(0.5)

    # Create a dataset and sort by the number of citations
    data = pd.DataFrame(list(zip(authors, titles, citations, links, etc)), index = [i+1 for i in range(len(authors))],
                        columns=['Author', 'Title', 'Citations', 'Source', 'Etc'])
    data.index.name = 'Number'

    # Sort by Citations
    data_ranked = data.sort_values(by='Citations', ascending=False)

    # Add columns with number of citations per year
    year_diff = now.year - year
    data_ranked.insert(4, 'cit/year', data_ranked['Citations'] / (year_diff + 1))
    data_ranked['cit/year'] = data_ranked['cit/year'].round(0).astype(int)

    # Add columns with number of citations per month 
    if month is not None:
        month_diff = now.month - month + 12 * year_diff
        data_ranked.insert(5, 'cit/month', data_ranked['Citations'] / (month_diff + 1))
        data_ranked['cit/month'] = data_ranked['cit/month'].round(0).astype(int)

    print(data_ranked)

    # Save results
    data_ranked.to_csv(os.path.join(csvpath, 'NeurIPS{}'.format(year)+'.csv'), encoding='utf-8') # Change the path

if __name__ == '__main__':
        main()