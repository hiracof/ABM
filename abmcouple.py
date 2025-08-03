import matplotlib
matplotlib.rcParams['font.family'] = 'Hiragino Sans'

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import random
import matplotlib.patches as patches

# === 設定 ===
N_total      = 100      # 男女各50名
space_size   = 50
speed        = 1.0
meet_dist    = 3.0
steps        = 180      # シミュレーション日数
threshold    = 0.8      # カップル成立閾値
break_prob   = 0.005    # 別れ確率

# 初期ペア設定
INITIAL_PAIR_RATE    = 0.332  
UNIV_MEET_RATE_NOAPP = 0.502
UNIV_MEET_RATE_APP   = 0.10

# === エージェント定義 ===
class Agent:
    def __init__(self, gender):
        self.gender         = gender
        self.x, self.y      = random.uniform(0, space_size), random.uniform(0, space_size)
        self.partner        = None
        self.attractiveness = random.random()
        self.met_at_univ    = False    # 大学内出会いフラグ
        self.meet_count     = 0        # 出会い頻度
    def move(self, t):
        # ステップ終了後は停止
        if t >= steps-1:
            return
        # ランダム移動
        angle = random.uniform(0, 2 * np.pi)
        self.x = (self.x + speed * np.cos(angle)) % space_size
        self.y = (self.y + speed * np.sin(angle)) % space_size

# === 初期化関数 ===
def initialize_agents(is_app=False):
    males   = [Agent('M') for _ in range(N_total//2)]
    females = [Agent('F') for _ in range(N_total//2)]
    seed_initial_pairs(males, females, is_app)
    return males, females, males + females

def seed_initial_pairs(males, females, is_app):
    num_pairs = int((len(males)+len(females)) * INITIAL_PAIR_RATE // 2)
    random.shuffle(males); random.shuffle(females)
    rate = UNIV_MEET_RATE_APP if is_app else UNIV_MEET_RATE_NOAPP
    for i in range(num_pairs):
        m, f = males[i], females[i]
        m.partner = f; f.partner = m
        if random.random() < rate:
            m.met_at_univ = f.met_at_univ = True

# 初期化
m_na, f_na, agents_na = initialize_agents(is_app=False)
m_ap, f_ap, agents_ap = initialize_agents(is_app=True)

history_na, history_ap = [], []
lines_na, lines_ap     = [], []

# === ビジュアル設定 ===
fig = plt.figure(figsize=(12,8))
gs  = fig.add_gridspec(2,2, height_ratios=[3,1])
ax_na    = fig.add_subplot(gs[0,0]); ax_na.set_title("アプリなし")
ax_ap    = fig.add_subplot(gs[0,1]); ax_ap.set_title("アプリあり")
ax_graph = fig.add_subplot(gs[1,:])
axes     = [ax_na, ax_ap]

# 枠線描画
for ax, col in zip(axes, ['blue','red']):
    rect = patches.Rectangle((0,0), space_size, space_size,
                             linewidth=2, edgecolor=col, facecolor='none')
    ax.add_patch(rect); ax.set_xlim(0,space_size); ax.set_ylim(0,space_size); ax.axis('off')

# 散布初期化
scat_na = ax_na.scatter([], [], s=40)
scat_ap = ax_ap.scatter([], [], s=40)

# ペア数比較グラフ
line_na, = ax_graph.plot([], [], label="アプリなし", color='blue')
line_ap, = ax_graph.plot([], [], label="アプリあり", color='red')
ax_graph.set_xlim(0,steps); ax_graph.set_ylim(0,N_total//2)
ax_graph.set_xlabel("日数"); ax_graph.set_ylabel("ペア数"); ax_graph.legend()

def update(t):
    global lines_na, lines_ap
    for l in lines_na: l.remove()
    for l in lines_ap: l.remove()
    lines_na, lines_ap = [], []

    ax_na.set_title(f"アプリなし（{t}日目）")
    ax_ap.set_title(f"アプリあり（{t}日目）")

    for (males, females, agents, scat, lines, history, app) in [
        (m_na, f_na, agents_na, scat_na, lines_na, history_na, False),
        (m_ap, f_ap, agents_ap, scat_ap, lines_ap, history_ap, True)
    ]:
        # 移動
        for a in agents: a.move(t)

        # 出会い頻度リセット
        for a in agents: a.meet_count = 0

        # ペアリング判定
        for m in males:
            if m.partner: continue
            candidates = []
            for f in females:
                if f.partner: continue
                dist = np.hypot(m.x-f.x, m.y-f.y)
                if dist < meet_dist:
                    candidates.append(f)
                    m.meet_count +=1; f.meet_count +=1
            if candidates:
                # ランダム選択
                f = random.choice(candidates)
                # アプリあり & 大学外出会いの場合は線を引かず、赤点のみ
                if app and not (m.met_at_univ and f.met_at_univ):
                    # 選んだ相手とは赤点としてペアリング
                    m.partner = f; f.partner = m
                else:
                    m.partner = f; f.partner = m

        # 別れ
        for m in males:
            if m.partner and random.random() < break_prob:
                m.partner.partner = None; m.partner = None

        # 点の更新
        pts = np.array([[a.x,a.y] for a in agents])
        colors = ['red' if a.partner else ('blue' if a.gender=='M' else 'green') for a in agents]
        scat.set_offsets(pts); scat.set_color(colors)

        # ペア線 (アプリありの大学外出会いは描画しない)
        if not app:
            for m in males:
                if m.partner:
                    f = m.partner
                    ln = plt.Line2D([m.x,f.x],[m.y,f.y],color='pink',alpha=0.5)
                    lines.append(ln); scat.axes.add_line(ln)
        else:
            for m in males:
                if m.partner and (m.met_at_univ and m.partner.met_at_univ):
                    f = m.partner
                    ln = plt.Line2D([m.x,f.x],[m.y,f.y],color='pink',alpha=0.5)
                    lines.append(ln); scat.axes.add_line(ln)

        # ペア数履歴
        p = sum(1 for a in agents if a.partner)//2
        history.append(p)

    line_na.set_data(range(len(history_na)), history_na)
    line_ap.set_data(range(len(history_ap)), history_ap)

    return scat_na, scat_ap, *lines_na, *lines_ap

ani = animation.FuncAnimation(fig, update, frames=steps, interval=100, blit=False)
plt.tight_layout()
plt.show()