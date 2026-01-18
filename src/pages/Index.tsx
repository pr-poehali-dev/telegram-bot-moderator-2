import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import Icon from '@/components/ui/icon';
import { toast } from 'sonner';

interface BotStats {
  total_users: number;
  banned_users: number;
  pending_reports: number;
  actions_24h: number;
}

const Index = () => {
  const [stats, setStats] = useState<BotStats>({
    total_users: 0,
    banned_users: 0,
    pending_reports: 0,
    actions_24h: 0
  });

  const [loading, setLoading] = useState(true);

  const BOT_TOKEN = '8107172432:AAEfZlmEo2i2_9w0JClHO0mgTv11oGAhQuk';
  const WEBHOOK_URL = 'https://functions.poehali.dev/43d82637-6a8c-4580-b7b3-04976e00403d';

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(false);
  };

  const setupWebhook = async () => {
    try {
      const response = await fetch(
        `https://api.telegram.org/bot${BOT_TOKEN}/setWebhook?url=${WEBHOOK_URL}`,
        { method: 'POST' }
      );
      const data = await response.json();
      
      if (data.ok) {
        toast.success('✅ Webhook подключен!');
      } else {
        toast.error('Ошибка: ' + data.description);
      }
    } catch (error) {
      toast.error('Ошибка подключения');
    }
  };

  const getWebhookInfo = async () => {
    try {
      const response = await fetch(
        `https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo`
      );
      const data = await response.json();
      
      if (data.ok) {
        const info = data.result;
        toast.info(`Webhook: ${info.url || 'Не установлен'}\nОбновлений: ${info.pending_update_count}`);
      }
    } catch (error) {
      toast.error('Ошибка получения информации');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        <div className="mb-8 text-center">
          <h1 className="text-5xl font-bold mb-3 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            🤖 Модерационный Бот
          </h1>
          <p className="text-gray-600 text-lg">
            Панель управления Telegram ботом
          </p>
        </div>

        <Alert className="mb-6 border-blue-200 bg-blue-50">
          <Icon name="Info" className="h-4 w-4" />
          <AlertDescription className="ml-2">
            <strong>Webhook URL:</strong> {WEBHOOK_URL}
          </AlertDescription>
        </Alert>

        <div className="grid md:grid-cols-3 gap-4 mb-8">
          <Button 
            onClick={setupWebhook}
            className="bg-green-600 hover:bg-green-700"
            size="lg"
          >
            <Icon name="Link" className="mr-2 h-5 w-5" />
            Подключить Webhook
          </Button>
          
          <Button 
            onClick={getWebhookInfo}
            variant="outline"
            size="lg"
          >
            <Icon name="Info" className="mr-2 h-5 w-5" />
            Проверить Webhook
          </Button>
          
          <Button 
            onClick={loadData}
            variant="outline"
            size="lg"
          >
            <Icon name="RefreshCw" className="mr-2 h-5 w-5" />
            Обновить данные
          </Button>
        </div>

        <div className="grid md:grid-cols-4 gap-4 mb-8">
          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-600">
                Всего пользователей
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center">
                <Icon name="Users" className="h-8 w-8 text-blue-500 mr-3" />
                <span className="text-3xl font-bold">{stats.total_users}</span>
              </div>
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-600">
                Забанено
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center">
                <Icon name="Ban" className="h-8 w-8 text-red-500 mr-3" />
                <span className="text-3xl font-bold">{stats.banned_users}</span>
              </div>
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-600">
                Жалобы
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center">
                <Icon name="AlertCircle" className="h-8 w-8 text-orange-500 mr-3" />
                <span className="text-3xl font-bold">{stats.pending_reports}</span>
              </div>
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-600">
                Действий (24ч)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center">
                <Icon name="Zap" className="h-8 w-8 text-purple-500 mr-3" />
                <span className="text-3xl font-bold">{stats.actions_24h}</span>
              </div>
            </CardContent>
          </Card>
        </div>

        <Tabs defaultValue="setup" className="space-y-6">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="setup">
              <Icon name="Settings" className="mr-2 h-4 w-4" />
              Настройка
            </TabsTrigger>
            <TabsTrigger value="commands">
              <Icon name="Terminal" className="mr-2 h-4 w-4" />
              Команды
            </TabsTrigger>
            <TabsTrigger value="roles">
              <Icon name="Shield" className="mr-2 h-4 w-4" />
              Роли
            </TabsTrigger>
          </TabsList>

          <TabsContent value="setup">
            <Card>
              <CardHeader>
                <CardTitle>Инструкция по подключению</CardTitle>
                <CardDescription>Следуйте этим шагам для запуска бота</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-4">
                  <div className="flex items-start gap-4">
                    <div className="flex items-center justify-center w-10 h-10 rounded-full bg-blue-100 text-blue-600 font-bold flex-shrink-0">
                      1
                    </div>
                    <div>
                      <h3 className="font-semibold mb-1">Создайте бота в Telegram</h3>
                      <p className="text-sm text-gray-600">
                        Найдите @BotFather в Telegram → /newbot → следуйте инструкциям
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start gap-4">
                    <div className="flex items-center justify-center w-10 h-10 rounded-full bg-green-100 text-green-600 font-bold flex-shrink-0">
                      2
                    </div>
                    <div>
                      <h3 className="font-semibold mb-1">Подключите Webhook</h3>
                      <p className="text-sm text-gray-600">
                        Нажмите кнопку "Подключить Webhook" выше
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start gap-4">
                    <div className="flex items-center justify-center w-10 h-10 rounded-full bg-purple-100 text-purple-600 font-bold flex-shrink-0">
                      3
                    </div>
                    <div>
                      <h3 className="font-semibold mb-1">Добавьте бота в чат</h3>
                      <p className="text-sm text-gray-600">
                        Добавьте бота в вашу группу и выдайте права администратора
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start gap-4">
                    <div className="flex items-center justify-center w-10 h-10 rounded-full bg-orange-100 text-orange-600 font-bold flex-shrink-0">
                      4
                    </div>
                    <div>
                      <h3 className="font-semibold mb-1">Готово!</h3>
                      <p className="text-sm text-gray-600">
                        Отправьте /start боту для проверки работы
                      </p>
                    </div>
                  </div>
                </div>

                <Alert className="border-green-200 bg-green-50">
                  <Icon name="CheckCircle2" className="h-4 w-4 text-green-600" />
                  <AlertDescription className="ml-2 text-green-800">
                    Бот полностью настроен и готов к работе! Все данные сохраняются в базе PostgreSQL.
                  </AlertDescription>
                </Alert>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="commands">
            <Card>
              <CardHeader>
                <CardTitle>Доступные команды</CardTitle>
                <CardDescription>Все команды модерации и управления</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  <div>
                    <h3 className="font-semibold mb-3 text-blue-600">🛡️ Модерация</h3>
                    <div className="grid gap-2">
                      <div className="p-3 bg-gray-50 rounded-lg">
                        <code className="text-sm font-mono">/ban [причина]</code>
                        <p className="text-sm text-gray-600 mt-1">Забанить пользователя (ответ на сообщение)</p>
                      </div>
                      <div className="p-3 bg-gray-50 rounded-lg">
                        <code className="text-sm font-mono">/mute [минуты] [причина]</code>
                        <p className="text-sm text-gray-600 mt-1">Мут пользователя на N минут</p>
                      </div>
                      <div className="p-3 bg-gray-50 rounded-lg">
                        <code className="text-sm font-mono">/kick [причина]</code>
                        <p className="text-sm text-gray-600 mt-1">Кикнуть пользователя из чата</p>
                      </div>
                      <div className="p-3 bg-gray-50 rounded-lg">
                        <code className="text-sm font-mono">/warn [причина]</code>
                        <p className="text-sm text-gray-600 mt-1">Предупреждение (3 варна = бан)</p>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h3 className="font-semibold mb-3 text-green-600">📝 Пользовательские</h3>
                    <div className="grid gap-2">
                      <div className="p-3 bg-gray-50 rounded-lg">
                        <code className="text-sm font-mono">/start</code>
                        <p className="text-sm text-gray-600 mt-1">Главное меню бота</p>
                      </div>
                      <div className="p-3 bg-gray-50 rounded-lg">
                        <code className="text-sm font-mono">/report [причина]</code>
                        <p className="text-sm text-gray-600 mt-1">Пожаловаться на сообщение</p>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h3 className="font-semibold mb-3 text-purple-600">🔍 Автопроверки</h3>
                    <div className="grid gap-2">
                      <div className="p-3 bg-purple-50 rounded-lg border border-purple-200">
                        <p className="text-sm font-medium">✅ Проверка на ботов</p>
                        <p className="text-sm text-gray-600 mt-1">Автоматически детектирует bot-аккаунты</p>
                      </div>
                      <div className="p-3 bg-purple-50 rounded-lg border border-purple-200">
                        <p className="text-sm font-medium">✅ Проверка возраста</p>
                        <p className="text-sm text-gray-600 mt-1">Проверяет новые аккаунты без username</p>
                      </div>
                      <div className="p-3 bg-purple-50 rounded-lg border border-purple-200">
                        <p className="text-sm font-medium">✅ Проверка на спам</p>
                        <p className="text-sm text-gray-600 mt-1">Детектирует множественные ссылки</p>
                      </div>
                      <div className="p-3 bg-purple-50 rounded-lg border border-purple-200">
                        <p className="text-sm font-medium">✅ Чёрный список</p>
                        <p className="text-sm text-gray-600 mt-1">Автоматический бан при входе</p>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="roles">
            <Card>
              <CardHeader>
                <CardTitle>Роли администрации</CardTitle>
                <CardDescription>Иерархия ролей и их права</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="p-4 bg-red-50 border-l-4 border-red-500 rounded">
                    <h4 className="font-semibold text-red-700 mb-1">Ст администратор</h4>
                    <p className="text-sm text-gray-600">Полный доступ: модерация, управление, настройки</p>
                  </div>
                  <div className="p-4 bg-purple-50 border-l-4 border-purple-500 rounded">
                    <h4 className="font-semibold text-purple-700 mb-1">Куратор администрации</h4>
                    <p className="text-sm text-gray-600">Управление модераторами и настройками</p>
                  </div>
                  <div className="p-4 bg-blue-50 border-l-4 border-blue-500 rounded">
                    <h4 className="font-semibold text-blue-700 mb-1">Ст модератор</h4>
                    <p className="text-sm text-gray-600">Модерация и управление базовыми настройками</p>
                  </div>
                  <div className="p-4 bg-cyan-50 border-l-4 border-cyan-500 rounded">
                    <h4 className="font-semibold text-cyan-700 mb-1">Мл модератор</h4>
                    <p className="text-sm text-gray-600">Базовые функции модерации</p>
                  </div>
                  <div className="p-4 bg-green-50 border-l-4 border-green-500 rounded">
                    <h4 className="font-semibold text-green-700 mb-1">Ст следящий администрация</h4>
                    <p className="text-sm text-gray-600">Мониторинг и предупреждения</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default Index;