export const displayCustomerId = (id: string) =>
  id.replace(/^CUST-(\d+).*$/, "合成客户 $1");
