# tweet_ggjn
指定した[gogojungle](https://www.gogojungle.co.jp/)のシストレEAのフォワード結果をつぶやきます。  

# usage
1. src/config.iniにTwitterAPIの認証情報と監視したいEAのgogojungleのアドレスを入力してください。
2. `docker build -t tweet_ggjn .`
3. `docker run -itd --rm --name tweet_ggjn tweet_ggjn`