from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import sys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException  

def names_match(name1, name2):
  # Split both names into components based on spaces
  name1_parts = name1.split()
  name2_parts = name2.split()
  
  # Count the number of matching components
  match_count = sum(1 for part in name1_parts if part in name2_parts)
  
  # Consider it a match if there are at least 2 matching components
  return match_count >= 2

def main():
  # Parse args
  inputFilename = sys.argv[1]
  outputFilename = sys.argv[2]

  # Set up output file
  with open(outputFilename, "w") as f:
    f.write("IMSDB_Title,RT_Title,CriticScore,AudienceScore\n")

    # Initialize Chrome driver
    options = ChromeOptions()
    options.add_argument("--headless=new")
    # driver = webdriver.Chrome(options=options)
    driver = webdriver.Chrome()
    driver.get("https://www.rottentomatoes.com/")

    # Read input file
    with open(inputFilename, "r") as file:
      driver.get("https://www.rottentomatoes.com/")
      for line in file:
        found = False

        # Parse input
        if (", the" in line):
          line = line.replace(", the", "")
        parsed_input = line.strip()
        parsed_input = parsed_input.split(",")
        imsdb_title = parsed_input[0]
        imsdb_writers = parsed_input[1:]
        imsdb_writers_set = set(imsdb_writers)
        print("imsdb_writers: ", imsdb_writers)

        # Write IMSDB title to output file
        f.write(imsdb_title+",")

        # Search for movie
        try:
          search_bar = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "search-text")))
        except TimeoutException:
          f.write("ERROR\n")
          continue
        search_bar.click()
        print(imsdb_title)
        search_bar.send_keys(imsdb_title)
        search_bar.send_keys(Keys.RETURN)
        # search_submit = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "search-submit")))
        # search_submit.click()

        # Locate the search results component
        try:
          search_results = WebDriverWait(driver, 10).until(
          EC.presence_of_element_located((By.CSS_SELECTOR, "search-page-result[type='movie']"))
          )
        except TimeoutException:
          f.write("NOTFOUND\n") 
          continue 
        
        result_items = search_results.find_elements(By.CSS_SELECTOR, "search-page-media-row")  # Adjust the selector as necessary
        result_urls = [result.find_element(By.CSS_SELECTOR, "a[data-qa='info-name']").get_attribute("href") for result in result_items]
        # Iterate through the results
        for result in result_urls:
          driver.get(result)
          # Get list of writers from the movie's page
          movie_info = driver.find_element(By.ID, "info")
          li_elements = movie_info.find_elements(By.TAG_NAME, "li")
          if len(li_elements) < 6: # Defensive programming
            continue
          writers_element = li_elements[5]
          span_element = writers_element.find_element(By.CSS_SELECTOR, "span[data-qa='movie-info-item-value']")
          writer_links = span_element.find_elements(By.TAG_NAME, "a")
          rt_writers = [link.text for link in writer_links]
          print("rt_writers: ", rt_writers)

          # Check if the writers match      
          rt_writers_set = set(rt_writers)
          if rt_writers_set is None:
            continue

          common_writers = imsdb_writers_set.intersection(rt_writers_set)
          print("common_writers: ", common_writers)

          # Prepare sets to hold writers not found in the initial intersection
          unmatched_imsdb_writers = imsdb_writers_set - common_writers
          unmatched_rt_writers = rt_writers_set - common_writers
          print("unmatched_imsdb_writers: ", unmatched_imsdb_writers)
          print("unmatched_rt_writers: ", unmatched_rt_writers)

          if len(unmatched_imsdb_writers) != 0 or len(unmatched_rt_writers) != 0:
            for writer1 in unmatched_imsdb_writers:
              # Check against each writer in the second set
              for writer2 in unmatched_rt_writers:
                  # If a match is found based on our custom logic, add to the common writers set
                  if names_match(writer1, writer2):
                      common_writers.add(writer1)
                      unmatched_rt_writers.discard(writer2)
                      break  # Move on to the next writer after finding a match

          unmatched_imsdb_writers = unmatched_imsdb_writers - common_writers
          # If match found, get audience and critic scores and write to output file
          if len(unmatched_imsdb_writers) == 0 or len(unmatched_rt_writers) == 0:
            rt_title = driver.find_element(By.CLASS_NAME, "title").text

            try:
              scoreboard = WebDriverWait(driver, 10).until(
                  EC.presence_of_element_located((By.ID, "scoreboard"))
              )
              critic_score = scoreboard.get_attribute("tomatometerscore")
              audience_score = scoreboard.get_attribute("audiencescore")

            except TimeoutException:
              critic_score = "NOTFOUND"
              audience_score = "NOTFOUND"
              continue

            f.write(f"{rt_title},{critic_score},{audience_score}\n")
            found = True
            break
        
        if found == False:
          f.write("NOTFOUND\n")

  driver.quit()

if __name__ == "__main__":
    main()   


