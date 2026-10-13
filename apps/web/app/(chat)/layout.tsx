export default function ChatRootLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="chat-app-root">
      <a href="#chat-main-content" className="skip-link">
        Saltar al contenido
      </a>
      <div id="chat-main-content" tabIndex={-1}>
        {children}
      </div>
    </div>
  );
}
