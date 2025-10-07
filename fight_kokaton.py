import os
import random
import sys
import time
import pygame as pg


WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
NUM_OF_BOMBS = 5  # 爆弾の個数
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


class Bird:
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -5),
        pg.K_DOWN: (0, +5),
        pg.K_LEFT: (-5, 0),
        pg.K_RIGHT: (+5, 0),
    }
    img0 = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
    img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん（右向き）
    imgs = {  # 0度から反時計回りに定義する
        (+5, 0): img,  # 右
        (+5, -5): pg.transform.rotozoom(img, 45, 0.9),  # 右上
        (0, -5): pg.transform.rotozoom(img, 90, 0.9),  # 上
        (-5, -5): pg.transform.rotozoom(img0, -45, 0.9),  # 左上
        (-5, 0): img0,  # 左
        (-5, +5): pg.transform.rotozoom(img0, 45, 0.9),  # 左下
        (0, +5): pg.transform.rotozoom(img, -90, 0.9),  # 下
        (+5, +5): pg.transform.rotozoom(img, -45, 0.9),  # 右下
    }

    def __init__(self, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数 xy：こうかとん画像の初期位置座標タプル
        """
        self.img = __class__.imgs[(+5, 0)]
        self.rct: pg.Rect = self.img.get_rect()
        self.rct.center = xy

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.img = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.img, self.rct)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rct.move_ip(sum_mv)
        if check_bound(self.rct) != (True, True):
            self.rct.move_ip(-sum_mv[0], -sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.img = __class__.imgs[tuple(sum_mv)]
        screen.blit(self.img, self.rct)


class Beam:
    """
    こうかとんが放つビームに関するクラス
    """
    def __init__(self, bird: "Bird"):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん（Birdインスタンス）
        """
        self.img = pg.image.load(f"fig/beam.png")  # ビームSurface
        self.rct = self.img.get_rect()  # ビームRect
        self.rct.centery = bird.rct.centery  # こうかとんの中心縦座標
        self.rct.left = bird.rct.right  # こうかとんの右座標
        self.vx, self.vy = +5, 0

    # 課題2の拡張を継承：生存判定を返す
    def update(self, screen: pg.Surface) -> bool:
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        画面内にいる間は描画し True、画面外に出たら False を返す
        """
        self.rct.move_ip(self.vx, self.vy)
        alive = (check_bound(self.rct) == (True, True))
        if alive:
            screen.blit(self.img, self.rct)
        return alive


class Bomb:
    """
    爆弾に関するクラス
    """
    def __init__(self, color: tuple[int, int, int], rad: int):
        """
        引数に基づき爆弾円Surfaceを生成する
        引数1 color：爆弾円の色タプル
        引数2 rad：爆弾円の半径
        """
        self.img = pg.Surface((2 * rad, 2 * rad))
        pg.draw.circle(self.img, color, (rad, rad), rad)
        self.img.set_colorkey((0, 0, 0))
        self.rct = self.img.get_rect()
        self.rct.center = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        self.vx, self.vy = +5, +5

    def update(self, screen: pg.Surface):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        yoko, tate = check_bound(self.rct)
        if not yoko:
            self.vx *= -1
        if not tate:
            self.vy *= -1
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)


# --- 課題3: 爆発エフェクト（短寿命の点滅）を追加 ---
class Explosion:
    def __init__(self, center: tuple[int, int], life: int = 20):
        base = pg.image.load("fig/explosion.gif")  # 用意された画像を想定
        self.frames = [base, pg.transform.flip(base, True, True)]
        self.rct = self.frames[0].get_rect(center=center)
        self.life = life
        self.t = 0

    def update(self, screen: pg.Surface) -> bool:
        if self.life <= 0:
            return False
        frame = self.frames[(self.t // 2) % 2]
        screen.blit(frame, self.rct)
        self.t += 1
        self.life -= 1
        return self.life > 0


# 追加: シンプルなスコア表示（課題1で実装済み）
class Score:
    def __init__(self):
        self.font = pg.font.SysFont("HG創英角ﾎﾟｯﾌﾟ体", 30)
        self.color = (0, 0, 255)
        self.value = 0  # 撃墜数

    def add(self, n: int = 1):
        self.value += n  # 追加: スコア加算

    def update(self, screen: pg.Surface):
        self.img = self.font.render(f"スコア: {self.value}", True, self.color)
        screen.blit(self.img, (10, 600))


def main():
    pg.display.set_caption("たたかえ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load("fig/pg_bg.jpg")
    bird = Bird((300, 200))

    # bomb = Bomb((255, 0, 0), 10)
    # bombs = []  # 爆弾用の空のリスト
    # for _ in range(NUM_OF_BOMBS):  # NUM_OF_BOMBS個の爆弾を追加
    #     bomb = Bomb((255, 0, 0), 10)
    #     bombs.append(bomb)
    bombs = [Bomb((255, 0, 0), 10) for _ in range(NUM_OF_BOMBS)]

    beam = None  # ゲーム初期化時にはビームは存在しない（課題1の名残）
    score = Score()  # 追加: スコア
    beam_ins = []  # 課題1の変数は残す（未使用でも削除しない）

    # 課題2: 複数ビーム用リスト
    beams: list[Beam] = []
    # --- 課題3: 爆発エフェクトのリスト ---
    explosions: list[Explosion] = []

    clock = pg.time.Clock()
    tmr = 0

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                # スペースキー押下でBeamクラスのインスタンス生成（課題1）
                # beam = Beam(bird)
                # 課題2: 複数ビームとして追加
                beams.append(Beam(bird))

        screen.blit(bg_img, [0, 0])

        for bomb in bombs:
            if bird.rct.colliderect(bomb.rct):
                # ゲームオーバー時に，こうかとん画像を切り替え，1秒間表示させる
                bird.change_img(8, screen)
                pg.display.update()
                time.sleep(1)
                return

        # 課題2+3: ビーム×爆弾の衝突（命中で爆発を出す）
        hit_any = False
        for bi, b in enumerate(beams):
            for mi, m in enumerate(bombs):
                if b.rct.colliderect(m.rct):
                    score.add(1)
                    explosions.append(Explosion(m.rct.center))  # --- 課題3: ここで爆発 ---
                    beams[bi] = None
                    bombs[mi] = None
                    bird.change_img(6, screen)
                    hit_any = True
                    break
            if hit_any:
                break
        beams = [b for b in beams if b is not None]
        bombs = [m for m in bombs if m is not None]

        key_lst = pg.key.get_pressed()
        bird.update(key_lst, screen)

        # 課題2: 画面外の弾は捨てる
        for i, b in enumerate(beams):
            if not b.update(screen):
                beams[i] = None
        beams = [b for b in beams if b is not None]

        # （課題1）単発ビームの描画は残す
        # if beam is not None:
        #     beam.update(screen)

        for bomb in bombs:
            bomb.update(screen)

        # --- 課題3: 爆発の寿命を更新し、終わったら消す ---
        for i, ex in enumerate(explosions):
            if not ex.update(screen):
                explosions[i] = None
        explosions = [ex for ex in explosions if ex is not None]

        score.update(screen)
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
