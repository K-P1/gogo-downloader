# gogo-downloader
# note: some of these information may or maynot be accurate for newer versions released.
Anime Episode Downloader
========================

This script allows you to download anime episodes by scraping download links from a specified website and downloading the episodes with specified quality. Created by KP.

Prerequisites
-------------
1. Ensure you have the latest version of Mozila firefox installed.
2. Download the latest version of geckodriver from 'https://github.com/mozilla/geckodriver/releases'
3. Place the downloaded geckodriver in the same directory as this script.
4. Install the required Python libraries:
   - requests
   - selenium
   - BeautifulSoup4
   - tqdm
   - python-dotenv

   You can install these libraries by running install.bat:


5. Create a gogoanime account here 'https://anitaku.pe/login.html' then create a `.env` file in the same directory as the script with and add your gogoanime email and password


How to Use the Script
---------------------
1. **Setup the Download List:**
- Create a file named `dl_list.txt` in the same directory as the script.
- `dl_list.txt` will be created automatically in newer versions, just run the scripts once and the file will be created, update it with the list of anime you want to download.
- Add the file save name, anime name and episode range to download in the following format:
- You can use whatever you want as the Nickname/Save-name. this will be used to create the folder your anime will be downloaded into.
- For the anime name go to gogoanime and get the exact anime name from the url bar for example: if this is the content of the url bar 'https://anitaku.pe/category/100-man-no-inochi-no-ue-ni-ore-wa-tatteiru' copy everything after category/ EXACTLY AS IT IS!!!, thats the anime name.
- For the episode you can use '&',',','-' as seperators; ',' is used for multiple exact episodes| '&' is used for two episodes| '-' is used for a range of episodes.
  ```
  naruto 1-5
  bleach-dub 1&9
  avatar-sub 4,5,9
  ```

2. **Running the Script:**
- Open a terminal or command prompt in the directory containing the script.
- Run the script using Python:
  ```
  python gogo_[version].py
  ```

3. **Using the Script:**
- The script will prompt you whether to use `dl_list.txt` for download list:
  ```
  Do you want to use dl_list.txt for download list? (yes/no):
  ```
  Enter `yes` or `no`.
  - If `yes`, the script will read from `dl_list.txt` and process each line.
  - If `no`, you will be prompted to enter the following details:
    - Save name
    - Anime name
    - Episode range (e.g., 1-23 for multiple or 23 for single)
    - Quality (1 for low to 4 for high)

4. **After Download:**
- Successfully downloaded episodes will be saved in a folder named after the Nickname you provided, if none was provided the anime name will be used.
- If the download fails for any reason, the failed download links will be saved in a file named `{anime_name}_failed_downloads.txt`.
- in newer versions the failed download will be automatically retried.
- The `dl_list.txt` will be updated to remove successfully downloaded lines.

Troubleshooting
---------------
1. **WebDriver Errors:**
- Ensure the ChromeDriver executable is in your PATH or the correct path is specified in the script.

2. **Missing .env File:**
- Ensure the `.env` file is in the same directory as the script and contains your email and password.

3. **Invalid Episode Format:**
- Ensure the episode range is specified correctly (e.g., 1-23 for multiple episodes).

4. **Quality Specification:**
- Enter a valid quality value (1, 2, 3, or 4).

Disclaimer
-------
The `gogo-downloader` script is provided "as is" without any warranties of any kind, either express or implied. The creator, KP, and contributors assume no responsibility for any errors, omissions, or damages arising from the use of this script. By using this script, you agree to the following:

1. **Compliance with Terms of Service:** You are solely responsible for ensuring that your use of this script complies with the terms of service of the websites being accessed, including but not limited to `gogoanime` and any other associated services.

2. **Intellectual Property:** This script is intended for personal use only. Any unauthorized use or distribution of content downloaded using this script may infringe on the intellectual property rights of others. It is your responsibility to ensure that you have the legal right to download and use the content.

3. **Security and Privacy:** You must handle your `.env` file and any personal credentials securely. The creator of this script is not responsible for any loss or unauthorized access to your personal information.

4. **Limitation of Liability:** In no event shall the creator or contributors be liable for any indirect, incidental, special, consequential, or punitive damages, or any loss of profits or data, whether in an action in contract or tort, arising from the use or inability to use this script.

5. **Updates and Maintenance:** The script may be updated or modified over time. The creator does not guarantee ongoing support or maintenance for any issues that may arise.

By using this script, you acknowledge that you have read, understood, and agree to these terms.

---

Feel free to adjust it based on your needs!

Contact
-------
For any issues or questions, please contact [Ayokunlegaye@gmail.com].

Enjoy!