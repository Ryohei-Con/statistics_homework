import re
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup, Tag

HTML_DIR = Path("./scraping/downloaded_html")


def get_cell_lines(cell: Tag):
    """
    セルの中身を改行で分割してリスト化する関数
    """
    if not cell:
        return []
    else:
        return list(cell.stripped_strings)


def clean_rank(rank_text):
    if rank_text.isdigit():
        return rank_text
    else:
        try:
            int(rank_text)
            return int(rank_text)
        except ValueError:
            return 6


def make_result_csv(file_path: Path):
    with open(file_path, "r") as f:
        html_text = f.read()

    soup = BeautifulSoup(html_text, "html.parser")

    # 結果データを格納するリスト
    data = []

    # 結果テーブルを探す
    # ボートレース公式サイトの構造に基づき、結果が表示されているテーブルを特定
    # 通常、クラス名 `is-w496` または `table1` などが使われるが、
    # 確実なのは "着" "枠" などのヘッダーを持つテーブル、またはtbody内の行構成から判断
    tables = soup.find_all('table')

    target_table = None
    for table in tables:
        # テーブル内のテキストに "着" と "ボートレーサー" または "選手" が含まれているか確認
        if ('着' in table.text) and ('ボートレーサー' in table.text):
            target_table = table
            break

    rows = target_table.find_all('tbody')
        
    for row in rows:
        # 各行のセルを取得
        cols = row.find_all('td')

        # データ行であるか簡易チェック（列数が十分にあるかなど）
        # 通常の結果行は4列以上あるはず
        if len(cols) < 4:
            continue

        # テキストデータの抽出と整形
        row_text = [c.get_text(strip=True) for c in cols]

        # 着順の取得（通常1列目）
        # 「落」などの場合は6にする
        rank_text = clean_rank(row_text[0])

        # 枠番の取得（通常2列目）
        frame_text = row_text[1]

        # 登録番号（ボートレーサー）の取得
        # 選手情報が含まれるセルを探す（通常3列目）
        racer_cell = cols[2]

        # 登録番号は通常4桁の数字。正規表現で探す
        # セル内のテキスト全てから探す
        racer_text = racer_cell.get_text(strip=True)
        racer_id = racer_text[:4]

        data.append({
            'レーサーid': racer_id,
            '枠番': frame_text,
            '着順': rank_text
        })

    # データフレームの作成
    df = pd.DataFrame(data)
    df = convert_fullwidth_to_halfwidth(df.copy())
    return df


def make_odds_csv(file_path: Path):
    with open(file_path, "r") as f:
        html_text = f.read()

    soup = BeautifulSoup(html_text, "html.parser")

    data = []

    # オッズが表示されているテーブルを探す
    # "単勝" という文字が含まれているテーブルを対象とする
    tables = soup.find_all('table')
    target_table = None

    for table in tables:
        # テーブル内のヘッダー等に '単勝' が含まれているか確認
        if '単勝' in table.get_text():
            target_table = table
            break
    rows = target_table.find_all('tbody')

    for row in rows:
        cols = row.find_all("td")
        row_text = [c.get_text(strip=True) for c in cols]
        data.append({
            "枠番": row_text[0],
            "単勝オッズ": row_text[2]
        })

    df = pd.DataFrame(data)
    df = convert_fullwidth_to_halfwidth(df.copy())
    return df


def make_race_csv(file_path: Path):
    with open(file_path, "r") as f:
        html_text = f.read()

    soup = BeautifulSoup(html_text, "html.parser")
    tables = soup.find_all('table')
    for table in tables:
        text = table.get_text()
        if '枠' in text and 'ボートレーサー' in text:
            target_table = table
            break

    data_list = []

    if target_table:
        # 行（tbody内のtr）を取得
        # 出走表の行は、1人の選手につき複数行（またはrowspan）で構成されることが多い
        # `tbody` タグごとに1選手の情報がまとまっているケースが多いので、tbodyを探す
        tbodies = target_table.find_all('tbody')

        # tbody単位でループ（各選手）
        for tbody in tbodies:
            # 1つのtbodyの中に複数のtrがある（通常4行程度）
            rows = tbody.find_all('tr')
            
            # 1行目（主要データ）
            row1 = rows[0]
            cols = row1.find_all('td')
            
            # データ抽出用変数の初期化
            waku = None
            age = None
            weight = None
            st_avg = None
            national_win = None
            national_2ren = None
            national_3ren = None
            local_win = None
            local_2ren = None
            local_3ren = None
            motor_2ren = None
            motor_3ren = None

            # --- 解析ロジック ---
            # カラムの位置はサイトのレイアウトに依存するが、一般的な出走表を想定
            # 1. 枠番 (class="is-boatColorX" など)
            # 2. 選手情報 (画像, 登番, 名前, 支部, 年齢, 体重, 級別)
            # 3. F/L
            # 4. 平均ST
            # 5. 全国成績 (勝率, 2連, 3連)
            # 6. 当地成績 (勝率, 2連, 3連)
            # 7. モーター (No, 2連, 3連)
            # 8. ボート (No, 2連, 3連)

            # テキスト取得と整形
            # 枠番
            waku_cell = row1.find(class_=re.compile('is-boatColor'))
            waku = waku_cell.get_text(strip=True)

            # 選手情報セル（名前や年齢が入っている大きなセル）
            # 通常、枠番の次にある
            # 年齢と体重を探す
            # 例: "福岡 35歳 / 52.0kg" のようなテキストが含まれる
            full_text = tbody.get_text(" ", strip=True) # tbody全体から探す方が確実
            
            # 年齢: "XX歳"
            age_match = re.search(r'(\d{2})歳', full_text)
            if age_match:
                age = age_match.group(1)
                
            # 体重: "XX.Xkg"
            weight_match = re.search(r'(\d{2,3}\.\d)kg', full_text)
            if weight_match:
                weight = weight_match.group(1)

            # 平均ST
            # "F" や "L" の隣、または "ST" ヘッダーに対応する列
            # 通常、独立したセルにある (例: "0.15")
            # 列のインデックスで特定するのが難しい場合、正規表現で "0.XX" を探すが、
            # 他の率と混ざる可能性がある。
            # HTML構造的に、平均STは通常特定のクラスを持つか、4列目あたり。
            # 取得した全テキストの中で "平均ST" の値を探すのは危険。
            # セルごとに見ていく。

            # 全国成績・当地成績・モーター
            # これらは <br> で区切られて1つのセルに入っていることが多い
            # 例: 
            # <td>7.40 <br> 50.00 <br> ...</td>

            # 抽出ロジックの強化: 列の位置推定
            # cols[0]: 枠
            # cols[1]: 選手画像・名前など
            # cols[2]: 級別など?
            # ...
            # 全国成績のセル、当地成績のセル、モーターのセルを特定する
            # 全国成績セルは通常、数値が3つ並んでいる (勝率, 2連, 3連)
            # 当地も同様。

            # セルを走査してパターンマッチ
            stat_cells = [get_cell_lines(col) for col in cols[4:]]
            # stat_cells には [全国, 当地, モーター, ボート] の順に入っていると推測

            # 全国
            nat_data = stat_cells[0]
            national_win = nat_data[0]
            national_2ren = nat_data[1]
            national_3ren = nat_data[2]

            # 当地
            loc_data = stat_cells[1]
            local_win = loc_data[0]
            local_2ren = loc_data[1]
            local_3ren = loc_data[2]
            
            # モーター
            # 通常: No, 2連, 3連
            mot_data = stat_cells[2]
            motor_2ren = mot_data[1]
            motor_3ren = mot_data[2]

            # 平均STの取得
            # 平均STは通常 "0.XX" の形式で、stat_cells に含まれない（1行しかないため）セルにある
            st_avg = get_cell_lines(cols[3])[2]

            # 平均STが見つからない場合、2行目以降にある可能性（公式サイトは1行目にある）
            # ただし、スタート展示のSTではなく「平均ST」

            data_list.append({
                '枠番': waku,
                '年齢': age,
                '体重': weight,
                '平均ST': st_avg,
                '全国-勝率': national_win,
                '全国-2連率': national_2ren,
                '全国-3連率': national_3ren,
                '当地-勝率': local_win,
                '当地-2連率': local_2ren,
                '当地-3連率': local_3ren,
                'モーター-2連率': motor_2ren,
                'モーター-3連率': motor_3ren
            })
    df = pd.DataFrame(data_list)
    df = convert_fullwidth_to_halfwidth(df.copy())
    return df


def convert_fullwidth_to_halfwidth(df: pd.DataFrame) -> pd.DataFrame:
    """DataFrame内の全角数字を半角数字に変換します。"""

    # 変換対象の全角数字と対応する半角数字のマップを作成
    # 0から9までの全角数字を対象とします
    zenkaku_map = {
        '０': '0', '１': '1', '２': '2', '３': '3', '４': '4',
        '５': '5', '６': '6', '７': '7', '８': '8', '９': '9',
        '．': '.' # 全角の小数点も考慮する場合
    }

    # 全ての列に対して処理を適用
    for col in df.columns:
        # object型（文字列）の列のみを対象とする
        if df[col].dtype == 'object':
            # 複数回のreplaceを適用するよりも、str.translateを使う方が効率的だが、
            # pandasではstr.replaceを連鎖させる方法も一般的。
            # 今回はシンプルにstr.replaceで処理します。

            # str.replace(全角文字, 半角文字, regex=False) を連鎖させる
            s = df[col].astype(str)
            for z, h in zenkaku_map.items():
                s = s.str.replace(z, h, regex=False)
            df[col] = s
    df = df.apply(
        pd.to_numeric,
        errors="coerce"
    )

    return df


def main():
    all_dfs = []
    num_race = len(list(HTML_DIR.iterdir()))
    for i, race_dir in enumerate(HTML_DIR.iterdir()):
        race_df = make_race_csv(race_dir / "race.html")
        # print(f"race_df\n{race_df}")
        odds_df = make_odds_csv(race_dir / "odds.html")
        # print(f"odds_df\n{odds_df}")
        result_df = make_result_csv(race_dir / "result.html")
        # print(f"result_df\n{result_df}")
        df = pd.merge(race_df, odds_df, on="枠番")
        df = pd.merge(df, result_df, on="枠番")
        # print(df.head())
        all_dfs.append(df)
        if i % 50 == 0:
            print(f"{i}/{num_race}")

    all_df = pd.concat(all_dfs, axis=0)
    all_df.to_csv("./make_csv/boat-race.csv")


if __name__ == "__main__":
    main()
