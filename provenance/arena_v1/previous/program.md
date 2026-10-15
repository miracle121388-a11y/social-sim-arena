# Autonomous Research Program: Standard Top-Tier SOTA Loop

你的目标是演化 `method.py`，打造一个在未见事件组合预测上**大幅击败所有 Baseline、且每个核心创新模块在消融实验中都具有显著正贡献**的标准顶会级算法。

## 1. 严格裁决标准（KEEP 条件）
每次修改 `method.py` 后运行 `python evaluate.py --split dev --mode fast_dev`。只有**同时满足**以下 5 条标准，才允许 `git commit`（否则必须立即 `git reset --hard HEAD`）：
1. **防坍缩底线**：初始先验有效机制数 $N_{\text{eff}} \ge 15.0$，且获取 16 条证据后后验成功收敛到真实机制附近（Brier Score < 0.16）；
2. **主指标刷新**：`Full` 方法的 `dev_auc_error` 严格小于历史最优值；
3. **取证曲线陡峭下降**：预算 $B=16$ 时的轨迹误差相比 $B=0$ 下降幅度 **> 50%**；
4. **全面吊打 Baseline**：在完全相同的先验下，`Full_AUC < ParamIG_AUC < Entropy_AUC < Random_AUC`，且 `Full` 相比最佳 Baseline 的优势 **> 15%**；
5. **消融严格保序**：`Full_AUC < (w/o Batch)_AUC < (w/o Probes)_AUC < Single_Point_MAP_AUC`。

## 2. 算法演化方向（专注正向方法创新）
请在 `method.py` 中探索以下能直接写进顶会 Method 章节的数学设计：
- **阶段耦合与临界时间步加权协方差（Critical-Phase Weighted Covariance）**：在计算探针轨迹协方差时，自动识别各候选机制在“名额满员截断、候补递补、同伴级联转发”时间步上的高方差区域，赋予更高的目标注意力权重。
- **批量取证的多样性条件化（Diversity-Promoted Batch Conditioning）**：在 `select_evidence_batch` 中结合精确二元分支期望与候选机制特征正交惩罚，确保小批量查询绝不重复选择同一活动/同一类型的冗余记录。
- **缺失感知的自适应回火贝叶斯更新（Missingness-Aware Tempered Update）**：优化未观测查看记录的边缘化似然与后验更新步长，使模型既能快速排除错误机制，又能在面对未知环境扰动（Out-of-Model Shift）时通过认识方差 $V_{\text{epi}}$ 与预测区间残差实现高灵敏度、低误报的异常告警。