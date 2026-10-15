import { Image } from "antd";
import { Header, Footer } from "../components/Layout";
import { shots, asset } from "../demo/scenarios";
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
                <figcaption>{title}</figcaption>
              </figure>
            ))}
          </div>
        </Image.PreviewGroup>
      </main>
      <Footer />
    </>
  );
}
