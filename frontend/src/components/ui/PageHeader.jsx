export default function PageHeader({ icon: Icon, kicker, title, description, action }) {
  return (
    <header className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
      <div>
        {kicker && <div className="page-kicker">{Icon && <Icon size={15} />}{kicker}</div>}
        <h1 className="page-title">{title}</h1>
        {description && <p className="page-copy">{description}</p>}
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </header>
  )
}
