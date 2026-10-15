export const displayCustomerId = (id: string) =>
  id.replace(/^SYN-V2-(\d+).*$/, "合成客户 $1");
