export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="">
      <main>{children}</main>
    </div>
  );
}
