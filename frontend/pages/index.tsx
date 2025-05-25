import { NextPage } from 'next'
import Head from 'next/head'
import OmniCoreDashboard from '@/components/OmniCoreDashboard'

const Home: NextPage = () => {
  return (
    <>
      <Head>
        <title>OmniCore AI - Dashboard Empresarial</title>
        <meta name="description" content="Sistema de IA Empresarial para Automação de Processos" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <OmniCoreDashboard />
    </>
  )
}

export default Home