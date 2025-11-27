## プロジェクトの概要
本レポートでは競艇のレース情報や結果について、データセット作成から分析までを行った。

具体的には2024年SG, G1, G2, G3グレードのレースを対象に https://www.boatrace.jp/ からスクレイピングし、「枠番,年齢,体重,平均ST,全国-勝率,全国-2連率,全国-3連率,当地-勝率,当地-2連率,当地-3連率,モーター-2連率,モーター-3連率,単勝オッズ,レーサーid,着順」を変数としたcsvを作成した。その後、主にPandasのDataFrameを使い分析し、matplotlib.pyplotを用いて可視化した。

スクレイプ対象の大会は以下の3つのリンクから辿れる。
scrape_base_url.pyのBASE_URLSにリンクを追加することで、分析範囲を広げることが可能である。

    https://www.boatrace.jp/owpc/pc/race/gradesch?year=2024&hcd=01
    https://www.boatrace.jp/owpc/pc/race/gradesch?year=2024&hcd=02
    https://www.boatrace.jp/owpc/pc/race/gradesch?year=2024&hcd=03

## 実行手順
1. docker containerの中に入る
2. app/.venv/bin/activateで仮想環境を有効化
3. scrape_base_url.pyを実行し、収集されたhtmlは同階層内のdownloaded_htmlに保存される。
4. analyze_boat_race/make_csv.pyを実行し、同階層内にboat-race.csvが作成される
5. analysis.ipynbが実行できるようになる。
