import { Image } from "antd";
import { Header, Footer } from "../components/Layout";
import { shots, asset } from "../demo/scenarios";
const captions: Record<string, string> = {
  "01-fuling-overview": "公开产业背景、合成客群和经营研究入口。",
  "02-fuling-allocation": "比较有限客户经理工时下的任务取舍。",
  "03-fuling-customer-action": "核对入选客户的业务驱动、所需材料与停止条件。",
  "04-supplier-overview": "查看订单回款与支出的时间差及资金压力。",
  "07-supplier-contract": "区分条件型回款与固定日期回款。",
  "08-supplier-reconcile": "实际收付与观察余额必须一起核对。",
};
export default function Screenshots() {
  return (
    <>
      <Header />
      <main className="page">
        <p className="eyebrow">完整产品 · 本地实拍</p>
        <h1>真实系统截图</h1>
        <p className="section-intro">
          以下截图来自本地运行的完整产品，GitHub Pages
          使用同一业务逻辑制作交互式公开演示。点击可放大查看。
        </p>
        <Image.PreviewGroup>
          <div className="screens-grid">
            {shots.map(([id, title]) => (
              <figure key={id}>
                <Image
                  src={asset("assets/screenshots/" + id + ".png")}
                  alt={title}
                />
                <figcaption>
                  <strong>{title}</strong>
                  <p>{captions[id]}</p>
                </figcaption>
              </figure>
            ))}
          </div>
        </Image.PreviewGroup>
      </main>
      <Footer />
    </>
  );
}
