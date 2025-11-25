## プロジェクトの概要
本レポートでは競艇のレース情報や結果について、データセット作成から分析までを行った。

具体的には2024年SG, G1, G2, G3グレードのレースを対象にhttps://www.boatrace.jp/からスクレイピングし、「枠番,年齢,体重,平均ST,全国-勝率,全国-2連率,全国-3連率,当地-勝率,当地-2連率,当地-3連率,モーター-2連率,モーター-3連率,単勝オッズ,レーサーid,着順」を変数としたcsvを作成した。その後、PandasのDataFrameを主に使い分析し、可視化にはmatplotlib.pyplotを用いた。

スクレイプ対象の大会は以下の3つの中にある。
    "https://www.boatrace.jp/owpc/pc/race/gradesch?year=2024&hcd=01",
    "https://www.boatrace.jp/owpc/pc/race/gradesch?year=2024&hcd=02",
    "https://www.boatrace.jp/owpc/pc/race/gradesch?year=2024&hcd=03"

## 実行手順
docker containerの中に入る
app/.venv/bin/activateで仮想環境を有効化
scraping/downloaded_html内のファイルはすべて削除したため、scrape_base_url.pyを実行し、htmlを収集
analyze_boat_race/make_csv.pyを実行し、同階層内にboat-race.csvが作成される
analysis.ipynbが実行できるようになる。