<div align="center">

[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]

</div>

<br />
<div align="center">
  <a href="https://github.com/iyasha/financyka-bot">
    <img src="images/logo.png" alt="Logo" width="80" height="80">
  </a>

  <h3 align="center">FinancykaBot</h3>

  <p align="center">
    FinancykaBot is the ultimate financial management tool on Telegram!
    <br />
    <br />
    <a href="https://github.com/iYasha/financyka-bot/issues">Report Bug</a>
    ·
    <a href="https://github.com/iYasha/financyka-bot/issues">Request Feature</a>
  </p>
</div>


With FinancykaBot, you can effortlessly store and organize your income and expenses transactions. This intelligent bot goes above and beyond by aggregating your financial data, providing valuable insights, and guiding you towards optimizing your financial flow. Say goodbye to the hassle of manual tracking and welcome a smarter way to enhance your financial well-being with FinancykaBot.
Based on [aiogram](https://github.com/aiogram/aiogram).

## Requirements
- [Python 3.9+](https://www.python.org/downloads/)
- [Poetry](https://python-poetry.org/docs/#installation)
- [Telegram Bot Token](https://core.telegram.org/bots#how-do-i-create-a-bot)

## Getting Started:  
* Clone the repository: `git clone https://github.com/iYasha/financyka-bot.git`  
* Install all dependencies:   `cd financyka-bot && poetry install`  
* Create a `.env` file:   `cp example.env .env`
* Fill in your bot token in `.env`:   `BOT_TOKEN=YOUR_TOKEN_HERE`   
* Enable shell:   `poetry shell`  
* Install spacy model:  `python -m spacy download ru_core_news_md`  
* Run the main script:  `python src/main.py`   

## Roadmap
 - [x] Add future transactions
 - [x] Add regular transactions
 - [x] Add AI model for transactions classification
 - [x] Add categories for transactions
 - [x] Add NER for transaction recognition
 - [x] Add ability to see budget for day and balance
 - [x] Add ability to create and join companies
 - [ ] Add ability to create wallets and use them in transactions
 - [ ] Add ability to scrape information from mobile banking
   - [ ] MonoBank
   - [ ] OTP Bank
   - [ ] PrivatBank (Impossible to do because of the lack of [API](https://api.privatbank.ua/#p24/orders))
 - [ ] Add synchronization with Personal Shop Accounts
   - [ ] Silpo
   - [ ] ATB
   - [ ] Rozetka
 - [ ] Add ability to create financial goals
 - [ ] Add ability to create financial predictions
 - [ ] Add financial recommendations based on user's goals and predictions

## Contributing
Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<!-- LICENSE -->
## License
Distributed under the MIT License. See `LICENSE` for more information.

## Contact
If you have any questions, feel free to contact me via email: [ivan@simantiev.com](mailto:ivan@simantiev.com)

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/iyasha/financyka-bot.svg?style=for-the-badge
[contributors-url]: https://github.com/iyasha/financyka-bot/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/iyasha/financyka-bot.svg?style=for-the-badge
[forks-url]: https://github.com/iyasha/financyka-bot/network/members
[stars-shield]: https://img.shields.io/github/stars/iyasha/financyka-bot.svg?style=for-the-badge
[stars-url]: https://github.com/iyasha/financyka-bot/stargazers
[issues-shield]: https://img.shields.io/github/issues/iyasha/financyka-bot.svg?style=for-the-badge
[issues-url]: https://github.com/iyasha/financyka-bot/issues
[license-shield]: https://img.shields.io/github/license/iyasha/financyka-bot.svg?style=for-the-badge
[license-url]: https://github.com/iyasha/financyka-bot/blob/master/LICENSE