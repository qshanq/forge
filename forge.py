import requests
import time

# APIキーとプレイヤー名
api_key = 'API'
player_name = 'IGN'  # プレイヤー名を指定

# UUIDを取得する関数
def get_uuid(api_key, player_name):
    url = f'https://api.hypixel.net/player?key={api_key}&name={player_name}'
    try:
        response = requests.get(url)
        response.raise_for_status()  # HTTPエラーチェック
        data = response.json()
        return data['player']['uuid']
    except requests.exceptions.RequestException as e:
        print(f"APIリクエストに失敗しました: {e}")
        return None
    except KeyError as e:
        print(f"UUIDの取得に失敗しました: {e}")
        return None

# アイテムごとの製作時間（ミリ秒）
forge_durations = {
    'GOLDEN_PLATE': 21600000,  # 6時間 = 21,600,000ミリ秒
    # 他のアイテムも必要に応じて追加
}

# Discord Webhookの設定
WEBHOOK_URL = "WEBHOOK"
USER_ID = "DISCORD_ID"  # メンションしたいユーザーのID

def format_time(milliseconds):
    total_seconds = milliseconds // 1000
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours}:{minutes:02}:{seconds:02}"

def send_webhook_message(message):
    data = {
        "content": f"<@{USER_ID}> {message}"  # メンションを含めたメッセージ
    }
    requests.post(WEBHOOK_URL, json=data)

# フォージングが完了したかどうかを追跡するフラグ
last_notification_sent = False

# UUIDを取得
uuid = get_uuid(api_key, player_name)

if uuid:
    url = f'https://api.hypixel.net/v2/skyblock/profiles?key={api_key}&uuid={uuid}'

    while True:
        try:
            response = requests.get(url)
            response.raise_for_status()  # HTTPエラーチェック
            data = response.json()  # レスポンスをJSONとして読み込む

            # 有効なプロフィールを取得
            profiles = data.get('profiles', [])
            if profiles:
                for profile in profiles:
                    members = profile.get('members', {})
                    member_data = members.get(uuid, {})
                    forge_processes = member_data.get('forge', {}).get('forge_processes', {})

                    for process_id, process in forge_processes.items():
                        for item_id, item in process.items():
                            if item['type'] == 'FORGING':
                                start_time = item['startTime']  # 製作開始時間
                                current_time = int(time.time() * 1000)  # 現在の時間（ミリ秒）
                                
                                # アイテムの製作時間を取得
                                forge_duration = forge_durations.get(item['id'], 0)

                                # 残り時間を計算
                                elapsed_time = current_time - start_time
                                remaining_time = forge_duration - elapsed_time

                                # 残り時間の表示
                                if remaining_time > 0:
                                    formatted_time = format_time(remaining_time)
                                    print(f"Process ID: {process_id}, Item: {item['id']}, Remaining Time: {formatted_time}")
                                else:
                                    print(f"Process ID: {process_id}, Item: {item['id']} has finished forging.")
                                    
                                    # 新しいフォージが始まるまで通知を送らない
                                    if not last_notification_sent:
                                        send_webhook_message(f"Process ID: {process_id}, Item: {item['id']} has finished forging.")
                                        last_notification_sent = True
                            else:
                                # フォージが終了した場合、last_notification_sentをリセット
                                last_notification_sent = False

            else:
                print("No valid profiles found.")

        except requests.exceptions.RequestException as e:
            print(f"APIリクエストに失敗しました: {e}")
        except KeyError as e:
            print(f"データに予期しないキーが見つかりません: {e}")
        
        # 5分（300秒）待機
        time.sleep(300)

else:
    print("UUIDの取得に失敗しました。プログラムを終了します。")